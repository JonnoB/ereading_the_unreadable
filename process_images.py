import marimo

__generated_with = "0.8.22"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import os
    import time
    from datetime import datetime
    import base64
    from helper_functions import (create_page_dict, scale_bbox, crop_and_encode_images, 
    knit_strings, knit_string_list, process_page, process_image_with_api)
    import io
    from pdf2image import convert_from_path
    from PIL import Image, ImageDraw, ImageFont
    import matplotlib.pyplot as plt
    import json
    from dotenv import load_dotenv
    import shutil
    from io import BytesIO
    from tqdm import tqdm

    import psutil
    import traceback
    import re

    from mistralai import Mistral
    load_dotenv()



    api_key = os.environ["MISTRAL_API_KEY"]
    model = "pixtral-12b-2409"

    client = Mistral(api_key=api_key)

    data_folder = 'data'
    save_folder = os.path.join(data_folder,'BLN600_mistral')
    os.makedirs(save_folder, exist_ok=True)
    return (
        BytesIO,
        Image,
        ImageDraw,
        ImageFont,
        Mistral,
        api_key,
        base64,
        client,
        convert_from_path,
        create_page_dict,
        crop_and_encode_images,
        data_folder,
        datetime,
        io,
        json,
        knit_string_list,
        knit_strings,
        load_dotenv,
        mo,
        model,
        np,
        os,
        pd,
        plt,
        process_image_with_api,
        process_page,
        psutil,
        re,
        save_folder,
        scale_bbox,
        shutil,
        time,
        tqdm,
        traceback,
    )


@app.cell
def __(data_folder, os):
    import wand.image
    from wand.display import display


    with wand.image.Image(filename=os.path.join(data_folder,'repeating.jpeg')) as img:
        img.deskew(0.4*img.quantum_range)
        img.save(filename=os.path.join(data_folder,'repeating_deskew.jpeg'))
        display(img)
    return display, img, wand


@app.cell
def __(
    BytesIO,
    Image,
    base64,
    datetime,
    knit_string_list,
    os,
    pd,
    process_image_with_api,
    time,
    tqdm,
    wand,
):
    def split_image(image, max_ratio=1.5, overlap_fraction=0.1, max_segments=10):
        """
        Split an image into segments based on a maximum aspect ratio.

        Args:
            image: PIL Image object
            max_ratio (float): Maximum width-to-height ratio before splitting
            overlap_fraction (float): Fraction of overlap between segments
            max_segments (int): Maximum number of segments to create

        Returns:
            list: List of PIL Image objects (segments)
        """
        width, height = image.size
        current_ratio = width / height

        if current_ratio <= max_ratio:
            return [image]

        segment_height = int(width / max_ratio)
        overlap_height = int(segment_height * overlap_fraction)

        segments = []
        y = 0
        while y < height and len(segments) < max_segments:
            bottom = min(y + segment_height, height)
            segment = image.crop((0, y, width, bottom))
            segments.append(segment)
            y = bottom - overlap_height

        return segments


    # Core process functions

    def initialize_log_file(output_folder):
        log_file_path = os.path.join(output_folder, 'processing_log.csv')
        if os.path.exists(log_file_path):
            log_df = pd.read_csv(log_file_path)
        else:
            log_df = pd.DataFrame(columns=['file_name', 'processing_time', 'input_tokens', 'output_tokens', 'total_tokens', 'sub_images', 'status', 'timestamp'])
        return log_file_path, log_df

    def load_image(file_path, deskew, output_folder):
        if deskew:
            with wand.image.Image(filename=file_path) as wand_img:
                wand_img.deskew(0.4 * wand_img.quantum_range)
                temp_path = os.path.join(output_folder, f"temp_deskewed_{os.path.basename(file_path)}")
                wand_img.save(filename=temp_path)
                img = Image.open(temp_path)
                os.remove(temp_path)
        else:
            img = Image.open(file_path)
        return img

    def process_image_segments(segments, prompt):
        content_list = []
        total_input_tokens = total_output_tokens = total_tokens = 0

        for i, segment in enumerate(segments):
            segment_content, usage = process_segment(segment, prompt)
            if segment_content and usage:
                content_list.append(segment_content)
                input_tokens, output_tokens, segment_total_tokens = usage
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens
                total_tokens += segment_total_tokens

        return content_list, total_input_tokens, total_output_tokens, total_tokens, len(segments)


    def process_segment(segment, prompt):
        buffered = BytesIO()
        segment.save(buffered, format="JPEG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        try:
            segment_content, usage = process_image_with_api(image_base64, prompt=prompt)
        except Exception as e:
            print(f"Error in process_image_with_api for segment: {str(e)}")
            segment_content, usage = None, None
        return segment_content, usage

    def save_text_output(output_folder, filename, content_list):
        combined_content = knit_string_list(content_list)
        output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(combined_content)

    def update_log(log_df, filename, processing_time, total_input_tokens, total_output_tokens, total_tokens, sub_images, status):
        log_entry = pd.DataFrame({
            'file_name': [filename],
            'processing_time': [processing_time],
            'input_tokens': [total_input_tokens],
            'output_tokens': [total_output_tokens],
            'total_tokens': [total_tokens],
            'sub_images': [sub_images],
            'status': [status],
            'timestamp': [datetime.now()]
        })
        return pd.concat([log_df[log_df['file_name'] != filename], log_entry], ignore_index=True)



    def process_jpeg_folder(folder_path, output_folder, prompt, max_ratio=1.5, overlap_fraction=0.1, deskew=True):
        os.makedirs(output_folder, exist_ok=True)
        log_file_path, log_df = initialize_log_file(output_folder)

        for filename in tqdm(os.listdir(folder_path)):
            if filename.lower().endswith(('.jpg', '.jpeg')) and filename not in log_df[log_df['status'] == 'Success']['file_name'].values:
                file_path = os.path.join(folder_path, filename)
                start_time = time.time()

                try:
                    img = load_image(file_path, deskew, output_folder)
                    segments = split_image(img, max_ratio, overlap_fraction)
                    content_list, total_input_tokens, total_output_tokens, total_tokens, sub_images = process_image_segments(segments, prompt)
                    save_text_output(output_folder, filename, content_list)
                    status = 'Success'
                except Exception as e:
                    print(f"Processing failed for {filename}: {str(e)}")
                    total_input_tokens = total_output_tokens = total_tokens = sub_images = 0
                    status = 'Failed'
                finally:
                    if 'img' in locals():
                        img.close()

                processing_time = time.time() - start_time
                log_df = update_log(log_df, filename, processing_time, total_input_tokens, total_output_tokens, total_tokens, sub_images, status)
                log_df.to_csv(log_file_path, index=False)

        return log_df

    return (
        initialize_log_file,
        load_image,
        process_image_segments,
        process_jpeg_folder,
        process_segment,
        save_text_output,
        split_image,
        update_log,
    )


@app.cell
def __():
    transcriber_prompt = "You are an expert at transcription. The text is from a 19th century news article. Please transcribe exactly the text found in the image. Do not add any commentary. Do not use mark up please transcribe using plain text only."

    return (transcriber_prompt,)


@app.cell
def __(mo):
    mo.md(r"""## With deskew""")
    return


@app.cell
def __(np, process_jpeg_folder, transcriber_prompt):

    process_jpeg_folder(folder_path = 'data/BLN600/Images_jpg', 
                        output_folder = 'data/BLN600_deskew',
                        prompt = transcriber_prompt, 
                         max_ratio=np.inf, overlap_fraction=0.2)

    process_jpeg_folder(folder_path = 'data/BLN600/Images_jpg', 
                        output_folder = 'data/BLN600_deskew_ratio_15',
                        prompt = transcriber_prompt, 
                         max_ratio=1.5, overlap_fraction=0.2)
    return


@app.cell
def __(mo):
    mo.md(r"""## Without Deskew""")
    return


@app.cell
def __(np, process_jpeg_folder, transcriber_prompt):
    process_jpeg_folder(folder_path = 'data/BLN600/Images_jpg', 
                        output_folder = 'data/BLN600_ratio_1000',
                        prompt = transcriber_prompt, 
                         max_ratio=np.inf, overlap_fraction=0.2, deskew =False)

    process_jpeg_folder(folder_path = 'data/BLN600/Images_jpg', 
                        output_folder = 'data/BLN600_ratio_15',
                        prompt = transcriber_prompt, 
                         max_ratio=1.5, overlap_fraction=0.2, deskew = False)
    return


@app.cell
def __(os, pd, re):
    import evaluate

    metric_cer = evaluate.load("cer")
    metric_wer = evaluate.load("wer")

    from markdown_it import MarkdownIt
    from mdit_plain.renderer import RendererPlain

    parser = MarkdownIt(renderer_cls=RendererPlain)


    def compute_metric(row, metric, prediction_col, reference_col):
        try:
            # Preprocess the text: lowercasing and replacing line breaks with spaces
            prediction = re.sub(r'\s+', ' ', row[prediction_col].lower().strip())
            #prediction = parser.render(prediction)
            reference = re.sub(r'\s+', ' ', row[reference_col].lower().strip())

            # Ensure the inputs to metric.compute are lists of strings
            predictions = [prediction]
            references = [reference]
            return metric.compute(predictions=predictions, references=references)
        except KeyError as e:
           #print(f"KeyError: {e} in row: {row}")
            return None
        except Exception as e:
            #print(f"Error: {e} in row: {row}")
            return None

    def load_txt_files_to_dataframe(folder_path, text_column_name):
        #Get list of .txt files
        txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]

        # Initialize lists to store data
        file_names = []
        file_contents = []

        # Read each file
        for file in txt_files:
            file_path = os.path.join(folder_path, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Append data to lists
            file_names.append(os.path.splitext(file)[0])  # Remove .txt extension
            file_contents.append(content)

        # Create DataFrame
        df = pd.DataFrame({
            'file_name': file_names,
            text_column_name: file_contents
        })

        return df

    def load_and_join_texts_as_dataframe(folder_list):
        result_df = None

        for folder_path in folder_list:
            # Extract the folder name from the path
            folder_name = os.path.basename(folder_path)

            # Load the text files from this folder
            df = load_txt_files_to_dataframe(folder_path, folder_name)
            df[folder_name] = df[folder_name].apply(lambda x: parser.render(x))
            # Rename the 'content' column to the folder name
            #df = df.rename(columns={'content': folder_name})

            if result_df is None:
                result_df = df
            else:
                # Perform a left join with the existing result
                result_df = result_df.merge(df, on='file_name', how='left')

        return result_df
    return (
        MarkdownIt,
        RendererPlain,
        compute_metric,
        evaluate,
        load_and_join_texts_as_dataframe,
        load_txt_files_to_dataframe,
        metric_cer,
        metric_wer,
        parser,
    )


@app.cell
def __(data_folder, load_and_join_texts_as_dataframe, os):
    df = load_and_join_texts_as_dataframe([os.path.join(data_folder, 'BLN600', 'Ground Truth'),
                                           os.path.join(data_folder, 'BLN600', 'OCR Text'),
                                          os.path.join(data_folder, 'BLN600_deskew'),
                                          os.path.join(data_folder, 'BLN600_deskew_ratio_15'),
                                          os.path.join(data_folder, 'BLN600_ratio_1000')])
    return (df,)


@app.cell
def __(compute_metric, df, metric_cer, metric_wer):
    df['cer_ocr'] = df.apply(compute_metric, axis=1, metric =metric_cer, prediction_col='OCR Text', reference_col='Ground Truth')
    df['wer_ocr'] = df.apply(compute_metric, axis=1, metric =metric_wer, prediction_col='OCR Text', reference_col='Ground Truth')

    df['cer_deskew_1000'] = df.apply(compute_metric, axis=1, metric =metric_cer, prediction_col='BLN600_deskew', reference_col='Ground Truth')


    df['cer_deskew_15'] = df.apply(compute_metric, axis=1, metric =metric_cer, prediction_col='BLN600_deskew_ratio_15', reference_col='Ground Truth')

    df['cer_nodeskew_1000'] = df.apply(compute_metric, axis=1, metric =metric_cer, prediction_col='BLN600_ratio_1000', reference_col='Ground Truth')

    return


@app.cell
def __(df):
    df[['file_name','cer_ocr', 'cer_deskew_1000', 'cer_deskew_15','cer_nodeskew_1000']].describe()
    return


@app.cell
def __(df):
    df2 = df.copy()
    df2['cer_diff_deskew'] = df2['cer_nodeskew_1000'] - df2['cer_deskew_1000']

    df2['cer_diff_ratio'] = df2['cer_deskew_1000'] - df2['cer_deskew_15']

    df2[['file_name', 'cer_diff_deskew', 'cer_diff_ratio' ]]
    return (df2,)


@app.cell
def __():
    import seaborn as sns
    return (sns,)


@app.cell
def __(df2, sns):
    sns.scatterplot(data = df2, x = 'cer_diff_deskew', y = 'cer_diff_ratio')
    return


if __name__ == "__main__":
    app.run()