import os 
import json 

from _utils import (
    create_directory,
    read_json_config,
    modify_output_config,
    modify_concurrency_config, 
    read_evaluate_log,
    get_files_with_extension, 
    reorder_list_substrings, 
    check_inputs_not_empty,
    start_workflow,
    load_input_template,
    check_path_dir,
    find_database,
    download_database
)

import argparse

script_dir = os.path.dirname(__file__)
config = read_json_config(os.path.join(script_dir, "config.json"))

# Command line argyments
parser = argparse.ArgumentParser(description='MetaBAT2 binnig, checkM assesment and GTDB-tk \
                                 taxonomical classification of MAGs', 
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-ir','--input_folder_reads', help='The directory with read in fastq.gz format', required=True)
parser.add_argument('-s1','--suffix1', help='Suffix of the first of the paired reads', 
                    type=str, default="_paired_1.fastq.gz", required=False)
parser.add_argument('-s2','--suffix2', help='Suffix of the second of the paired reads', 
                    type=str, default="_paired_2.fastq.gz", required=False)
parser.add_argument('-ic','--input_folder_contigs', help='The directory with contigs in .fa format', required=True)
parser.add_argument('-sc','--suffix', help='Suffix of the filename to be identified in contig folder & replaced in the output(i.e. -s .fa  -i ID7.fa -> ID7.fna)', 
                    type=str, default=".min500.contigs.fa")
parser.add_argument('-gtdb','--gtdbtk_data', help='Path to a diretory with GTDB database', required=True)

parser.add_argument('-o','--output_folder', help='The directory for the output', required=True)

parser.add_argument('-t', '--thread_num', help="Number of threads to use", type=int, default=1)
parser.add_argument('-c','--concurrent_jobs', help='Number of jobs to run in parallel', 
                    type=int, default=1, required=False)

args = vars(parser.parse_args())
system_folder = os.path.join(args["output_folder"], "system")
args["input_folder_reads"] = os.path.abspath(args["input_folder_reads"])
args["input_folder_contigs"] = os.path.abspath(args["input_folder_contigs"])
# checking if input directory exists
check_path_dir(args["input_folder_reads"])
check_path_dir(args["input_folder_contigs"])

gtdb = find_database(args["gtdbtk_data"], [config["gtdbtk_db_release"]], "gtdb")
if not gtdb:
    description = "It will allow to remove human contaminant DNA from samples."
    gtdb_folder = download_database(args["gtdbtk_data"], config["gtdb_url"],
                                      "gtdb", description)
    gtdb = find_database(gtdb_folder, [config["gtdbtk_db_release"]], "gtdb")

# Getting necessary files from script name
script_name = os.path.basename(__file__).split(".")[0]

# load input template
template = load_input_template(script_dir, script_name, config)
    
# collect reads from dir
forward_reads = get_files_with_extension(args["input_folder_reads"], args["suffix1"])
reverse_reads = get_files_with_extension(args["input_folder_reads"], args["suffix2"])
sample_ids = [x.split("/")[-1].split("_")[0] for x in forward_reads]
reverse_reads = reorder_list_substrings(reverse_reads, sample_ids)

# collect contigs from dir
contigs =  get_files_with_extension(args["input_folder_contigs"], args["suffix"])
contigs = reorder_list_substrings(contigs, sample_ids)

check_inputs_not_empty({"forward reads" : forward_reads, 
                       "reverse reads" : reverse_reads, 
                       "contigs" : contigs})

# fill the input template
for read_1, read_2, contig in zip(forward_reads, reverse_reads, contigs):
    template["predict_mags.sampleInfo"].append({"file_r1": read_1, 
                                                "file_r2": read_2, 
                                                "contigs": contig,
                                                "sample_id": contig.split("/")[-1].split(".")[0]}) 

template["predict_mags.thread_num"] = args["thread_num"]
template["predict_mags.gtdb_release"] = config["gtdbtk_db_release"]

# creating output directory
create_directory(args["output_folder"])
create_directory(system_folder)

# writing input json
inputs_path = os.path.join(system_folder, 'input_predict_mags.json')
with open(inputs_path, 'w') as f:
    json.dump(template, f, indent=4, sort_keys=True, ensure_ascii=False)


paths = {
    "config_path" : config["db_mount_config"], 
    "cromwell_path" : config["cromwell_path"], 
    "wdl_path" : config["wdls"][script_name],
    "output_config_path" : config["output_config_path"]
}

# creating absolute paths
for path in paths.keys():
    paths[path] = os.path.abspath(os.path.join(script_dir, paths[path]))

# modifying config to change output folder
paths["output_config_path"] = modify_output_config(paths["output_config_path"], args["output_folder"], system_folder)
# modifying config to change number of concurrent jobs and mount dbs
paths["config_path"] = modify_concurrency_config(paths["config_path"], 
                                                 system_folder,
                                                 gtdbtk_path=os.path.abspath(args["gtdbtk_data"]),
                                                 n_jobs=args["concurrent_jobs"])

# starting workflow 
log_path = start_workflow(paths, inputs_path, system_folder, script_name)

# checking if the job was successful
read_evaluate_log(log_path)