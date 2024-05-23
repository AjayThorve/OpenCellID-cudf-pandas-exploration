import requests
import gzip
import shutil
import os
from tqdm import tqdm
import pandas as pd

class OpenCellIDDownloader:
    def __init__(self, token, output_dir="opencellid_data"):
        self.base_url = "https://opencellid.org/ocid/downloads"
        self.token = token
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def download_and_extract_file(self, url, output_gz_path, output_csv_path):
        if os.path.exists(output_csv_path):
            print(f"CSV file already exists: {output_csv_path}")
            return

        if not os.path.exists(output_gz_path):
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            if response.status_code == 200:
                with open(output_gz_path, 'wb') as f, tqdm(
                    desc=f"Downloading {output_gz_path}",
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for data in response.iter_content(chunk_size=1024):
                        bar.update(len(data))
                        f.write(data)
                print(f"Downloaded: {output_gz_path}")
            else:
                print(f"Failed to download. Status code: {response.status_code}")
                return
        else:
            print(f"GZ file already exists: {output_gz_path}")

        if not os.path.exists(output_csv_path):
            with gzip.open(output_gz_path, 'rb') as f_in:
                with open(output_csv_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print(f"Extracted to {output_csv_path}")

    def download_us_dataset(self):
        us_files = []
        for mcc_code in range(311, 317):
            file_name = f"{mcc_code}.csv.gz"
            url = f"{self.base_url}?token={self.token}&type=mcc&file={file_name}"
            output_gz_path = os.path.join(self.output_dir, file_name)
            output_csv_path = os.path.join(self.output_dir, f"{mcc_code}.csv")
            print(f"Processing {file_name}...")
            self.download_and_extract_file(url, output_gz_path, output_csv_path)
            us_files.append(output_csv_path)
        
        self.concatenate_csv_files(us_files, os.path.join(self.output_dir, "cell_towers_us.csv"))

    def download_full_dataset(self):
        file_name = "cell_towers.csv.gz"
        url = f"{self.base_url}?token={self.token}&type=full&file={file_name}"
        output_gz_path = os.path.join(self.output_dir, file_name)
        output_csv_path = os.path.join(self.output_dir, "cell_towers.csv")
        print(f"Processing {file_name}...")
        self.download_and_extract_file(url, output_gz_path, output_csv_path)

    def concatenate_csv_files(self, file_list, output_path):
        if os.path.exists(output_path):
            print(f"Concatenated file already exists: {output_path}")
            return

        print(f"Concatenating files into {output_path}...")
        dataframes = [pd.read_csv(file, names=['radio', 'MCC', 'MNC', 'area', 'cell', 'unit', 'lon', 'lat', 'range',
       'samples', 'changeable', 'created', 'updated', 'averageSignal']) for file in file_list]
        concatenated_df = pd.concat(dataframes, ignore_index=True)
        concatenated_df.to_csv(output_path, index=False)
        print(f"Saved concatenated file to {output_path}")

# Usage example in a Jupyter notebook:
# from opencellid_downloader import OpenCellIDDownloader
# downloader = OpenCellIDDownloader(token="your_token_here")
# downloader.download_us_dataset()  # For US dataset
# downloader.download_full_dataset()  # For full dataset
