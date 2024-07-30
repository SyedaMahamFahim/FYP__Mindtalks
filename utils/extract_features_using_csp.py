import os
import numpy as np
from io import BytesIO
from mne.decoding import CSP
from utils.cloud_helper import upload_file_to_s3, upload_generated_file_to_s3
from utils.Data_extractions import extract_block_data_from_subject
from utils.Data_processing import filter_by_class, filter_by_condition, select_time_window

### ---- Processing Variables ---- ###

# Define CSP parameters
n_components = 50  # Number of CSP components
reg_param = 0.01
# Data filtering
datatype = "eeg"
Cond = "Inner"
Classes = "ALL"
# Time window
t_start = 0.5
t_end = 3
fs = 256  # Sampling rate

# Set the uploads folder path
UPLOAD_FOLDER = 'uploads'

# Ensure the uploads directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)



def extract_csp(local_file_path,root_dir, N_S, N_B):
    N_S=int(N_S)
    N_B=int(N_B)
    try:
        # .fif
        # Load all trials for a single subject
        X, Y = extract_block_data_from_subject(local_file_path,root_dir, N_S, datatype, N_B)
        print("Extracted from block")

        X = X.get_data()  # Convert EpochsFIF object to numpy array
        print("X shape:", X.shape)
        print("Y shape:", Y.shape)


        # Cut useful time. i.e action interval
        print("starting cut")
        X = select_time_window(X, t_start, t_end, fs)
        print("Cut useful time")
        print("X shape:", X.shape)
        print("Y shape:", Y.shape)


        # # Filter By condition i.e Inner
        X, Y = filter_by_condition(X, Y, condition='Inner')
        print("Filtered by condition")
        print("X shape:", X.shape)
        print("Y shape:", Y.shape)

        # # Filter By class i.e ALL classes
        X, Y = filter_by_class(X, Y, 'ALL')
        print("Filtered by class")
        print("X shape:", X.shape)
        print("Y shape:", Y.shape)

        # Initialize CSP with regularization
        csp = CSP(n_components=n_components, reg=reg_param, log=True, norm_trace=False)
        print("Initialized CSP")

        # Fit CSP on training data and transform data
        X_csp = csp.fit_transform(X, Y[:, 1])  # Assuming class labels are in the second column of Y

        return X_csp, Y
    except Exception as e:
        print(f"Error processing subject {N_S}: {e}")
        return None, None
    

all_features = []
all_labels = []

def extract_features_using_csp(local_file_path,root_dir,subject_no, session_no):
    try:
        N_S=subject_no
        N_B=session_no

        features, labels = extract_csp(local_file_path,root_dir, N_S, N_B)
        if features is not None and labels is not None:
            # Append the data to the lists
            all_features.append(features)
            all_labels.append(labels)

        # Stack all the features and labels
        X_data = np.vstack(all_features)
        Y_data = np.vstack(all_labels)
        print("Combined Features shape:", X_data.shape)
        print("Combined Labels shape:", Y_data.shape)
        print("First few combined features:\n", X_data[:1])
        print("First few combined labels:\n", Y_data[:1])


        local_file_name = f"perfect_file_subject_{N_S}_session_{N_B}_features.npz"
        file_path = os.path.join(UPLOAD_FOLDER, local_file_name)
        np.savez(file_path, features=X_data, labels=Y_data)
        print("Saving completed.")

        s3_url = upload_generated_file_to_s3(file_path, 'features_extraction')
        print(f"Uploaded file to S3: {s3_url}")
                # Delete the local file
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted local file: {file_path}")

        return s3_url

    
    
    except Exception as e:
        print(f"Error processing subject {N_S}: {e}")
        return None, None