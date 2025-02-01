"""
This script prepares and sends the images to Pixtral. It uses the post-processed bounding boxes
And sends the cropped images batched by issue. 

It contains three prompt types,

text
figure
table

"""

import pandas as pd
import numpy as np
import os
from mistralai import Mistral
from function_modules.send_to_lm_functions import process_issues_to_jobs

from pathlib import Path



# Change working directory to project root
os.chdir(Path(__file__).parent.parent)

# Dictionary mapping parquet files to their corresponding image folders
image_folder = os.environ['image_folder']
path_mapping = {
    'English_Womans_Journal_issue_PDF_files_1056.parquet': os.path.join(image_folder, 'converted/all_files_png_120/English_Womans_Journal_issue_PDF_files'),
    'Leader_issue_PDF_files_1056.parquet': os.path.join(image_folder, 'converted/all_files_png_120/Leader_issue_PDF_files'),
    'Monthly_Repository_issue_PDF_files_1056.parquet': os.path.join(image_folder, 'converted/all_files_png_120/Monthly_Repository_issue_PDF_files'),
    'Tomahawk_issue_PDF_files_1056.parquet': os.path.join(image_folder, 'converted/all_files_png_120/Tomahawk_issue_PDF_files'),
    'Publishers_Circular_issue_PDF_files_1056.parquet': os.path.join(image_folder, 'converted/all_files_png_120/Publishers_Circular_issue_PDF_files'),
    'Northern_Star_issue_PDF_files_2112.parquet': os.path.join(image_folder, 'converted/all_files_png_200/Northern_Star_issue_PDF_files')
}

# path_mapping = {
#     'Leader_issue_PDF_files_1040.parquet': '/media/jonno/ncse/converted/all_files_png_120/Leader_issue_PDF_files',
#     'English_Womans_Journal_issue_PDF_files_1040.parquet': '/media/jonno/ncse/converted/all_files_png_120/English_Womans_Journal_issue_PDF_files'
# }
# API setup
api_key = os.environ["MISTRAL_API_KEY"]
client = Mistral(api_key=api_key)

# Prompt dictionary
prompt_dict = {
    'text': """The text in the image is from a 19th century English newspaper, please transcribe the text including linebreaks. Do not use markdown use plain text only. Do not add any commentary.""",
    'figure': 'Please describe the graphic taken from a 19th century English newspaper. Do not add additional commentary',
    'table': 'Please extract the table from the image taken from a 19th century English newspaper as a tab separated values (tsv) text file. Do not add any commentary'
}

# Process each file
for parquet_file, image_path in path_mapping.items():
    # Construct full path to parquet file
    parquet_path = os.path.join('data/periodical_bboxes/post_process', parquet_file)
    
    # Load bbox dataframe
    bbox_df = pd.read_parquet(parquet_path)

    if True: # This is to allow testing on small datasets
        random_pages = bbox_df['filename'].unique()
        np.random.seed(4321) 
        random_pages = np.random.choice(random_pages, size=3, replace=False)

        # Filter the DataFrame to only include these pages
        bbox_df = bbox_df[bbox_df['filename'].isin(random_pages)]
    
    # Create output filename based on the base folder name
    base_name = os.path.basename(image_path)
    output_file = f'data/processed_jobs/ncse/{base_name}.csv'
    
    print(f"Processing {parquet_file}...")
    
    # Process the data
    process_issues_to_jobs(
        bbox_df=bbox_df,
        images_folder=image_path,
        prompt_dict=prompt_dict,
        client=client,
        output_file=output_file,
        deskew=False,
        max_ratio=1.5
    )
    
    print(f"Completed processing {parquet_file}")

print("All files processed!")