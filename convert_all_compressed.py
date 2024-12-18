from helper_functions import convert_pdf_to_image
import os
from tqdm import tqdm
import pandas as pd
from datetime import datetime
import traceback
import tarfile
import shutil

image_dpi = 120
save_folder = f'/media/jonno/ncse/converted/all_files_png_{image_dpi}'
source_folder = os.path.join('/media/jonno/ncse')

save_folder = f'data/converted/all_files_png_{image_dpi}'
source_folder = os.path.join('data/all_compressed')

# Modified subfolder names to include .tar.gz extension
subfolder_names = [
    'English_Womans_Journal_issue_PDF_files.tar.gz',
    'Leader_issue_PDF_files.tar.gz',
    'Monthly_Repository_issue_PDF_files.tar.gz',
    'Northern_Star_issue_PDF_files.tar.gz',
    'Publishers_Circular_issue_PDF_files.tar.gz',
    'Tomahawk_issue_PDF_files.tar.gz'
]

subfolder_names = os.listdir(source_folder)

# Define file paths
log_file = os.path.join(save_folder, 'conversion_log.csv')
page_info_file = os.path.join(save_folder, 'page_size_info.parquet')

# Initialize or load existing log
if os.path.exists(log_file):
    log_df = pd.read_csv(log_file)
else:
    log_df = pd.DataFrame(columns=['timestamp', 'subfolder', 'file', 'status', 'error_message'])

# Load existing page info if it exists
if os.path.exists(page_info_file):
    existing_page_info = pd.read_parquet(page_info_file)
else:
    existing_page_info = pd.DataFrame()

def update_log(subfolder, file, status, error_message=''):
    global log_df
    new_row = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'subfolder': subfolder,
        'file': file,
        'status': status,
        'error_message': error_message
    }
    log_df = pd.concat([log_df, pd.DataFrame([new_row])], ignore_index=True)
    log_df.to_csv(log_file, index=False)

def update_page_info(new_info, subfolder, file):
    global existing_page_info
    
    new_df = pd.DataFrame(new_info)
    new_df['subfolder'] = subfolder
    new_df['source_file'] = file
    
    if not existing_page_info.empty:
        existing_page_info = existing_page_info[
            ~((existing_page_info['subfolder'] == subfolder) & 
              (existing_page_info['source_file'] == file))]
    
    existing_page_info = pd.concat([existing_page_info, new_df], ignore_index=True)
    
    backup_file = page_info_file + '.backup'
    try:
        existing_page_info.to_parquet(backup_file)
        os.replace(backup_file, page_info_file)
    except Exception as e:
        print(f"Error saving page info: {str(e)}")

for compressed_subfolder in subfolder_names:
    print(f'Processing {compressed_subfolder}')
    
    # Remove .tar.gz to get the original folder name
    subfolder = compressed_subfolder.replace('.tar.gz', '')
    
    compressed_path = os.path.join(source_folder, compressed_subfolder)
    temp_extract_path = os.path.join(source_folder, subfolder)
    save_subfolder = os.path.join(save_folder, subfolder)
    os.makedirs(save_subfolder, exist_ok=True)

try:
        # Extract the compressed folder
        with tarfile.open(compressed_path, 'r:gz') as tar:
            tar.extractall(path=source_folder)

        # Process the files in the extracted folder
        file_names = os.listdir(temp_extract_path)
        
        for file in tqdm(file_names):
            # Check if file was already successfully processed
            if not log_df.empty and len(log_df[(log_df['subfolder'] == subfolder) & 
                                            (log_df['file'] == file) & 
                                            (log_df['status'] == 'success')]) > 0:
                continue

            try:
                page_info = convert_pdf_to_image(os.path.join(temp_extract_path, file), 
                                            output_folder=save_subfolder, 
                                            dpi=image_dpi, 
                                            image_format='PNG', 
                                            use_greyscale=True)
                
                update_page_info(page_info, subfolder, file)
                update_log(subfolder, file, 'success')
            except Exception as e:
                error_message = str(e) + '\n' + traceback.format_exc()
                update_log(subfolder, file, 'failed', error_message)

        # Clean up: remove the extracted folder after processing
        shutil.rmtree(temp_extract_path)
        print(f"Completed processing {subfolder} and cleaned up temporary files")

except Exception as e:
    error_message = f"Error processing {compressed_subfolder}: {str(e)}\n{traceback.format_exc()}"
    print(error_message)
    # Try to clean up if extraction happened but processing failed
    if os.path.exists(temp_extract_path):
        shutil.rmtree(temp_extract_path)