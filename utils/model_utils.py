import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_score, recall_score, f1_score, roc_curve, auc
import joblib
from tensorflow.keras.models import load_model
from tensorflow import keras  # Explicit import for TensorFlow 2 compatibility
import matplotlib.pyplot as plt
from sklearn.preprocessing import label_binarize
from utils.cloud_helper import upload_generated_file_to_s3,save_summary_to_dynamodb
import boto3
import io
import datetime
import seaborn as sns
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
import json

from decimal import Decimal

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

# Initialize the S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id='AKIAZI5FQSOV7GMA6JW4',
    aws_secret_access_key='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'
)

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
def evaluate_model(csp_file_name, model_path, scaler_path):


        # Load the .npz file
    with np.load(csp_file_name) as new_data:
        # Preprocess and clean numpy file
        labels = new_data['labels']
        labels = labels[:, 1]

        # Load features
        features = new_data['features']

    # Function to clean feature strings
    def clean_feature_string(feature_str):
        if isinstance(feature_str, str):
            cleaned = feature_str.strip('[]').replace(' ', ',').replace('\n', '')
            return cleaned.split(',') if cleaned else []
        return feature_str  # If it's already a list or array, return as is

    # Convert the feature strings to lists of floats
    cleaned_features = []
    for feature in features:
        cleaned_feature = clean_feature_string(feature)
        if len(cleaned_feature) == 0:
            cleaned_feature = [0.0] * 10  # Handle empty features by filling with placeholder
        cleaned_features.append([float(i) for i in cleaned_feature])

    # Convert cleaned_features to a numpy array
    X_new = np.array(cleaned_features)
    y_new = labels

    # Standardize features
    scaler = joblib.load(scaler_path)
    X_new = scaler.transform(X_new)

    # Reshape the data for the model if necessary (e.g., CNN input)
    X_new_transformed = X_new.reshape(X_new.shape[0], X_new.shape[1], 1)

    # Load the trained model
    model = load_model(model_path)

    # Predict and evaluate
    predictions = model.predict(X_new_transformed)
    predicted_classes = np.argmax(predictions, axis=1)
    accuracy = accuracy_score(y_new, predicted_classes)

    # Classification report
    report = classification_report(y_new, predicted_classes, output_dict=True)
    print('This is the classification report', report)

    # Confusion matrix
    conf_matrix = confusion_matrix(y_new, predicted_classes)

    # Plot the confusion matrix (example plot)
    plt.figure(figsize=(10, 7))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', xticklabels=np.unique(y_new), yticklabels=np.unique(y_new))
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    # Save the plot in the "images_upload" folder
    upload_folder = "images_upload"
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    local_file_name = f"confusion_matrix_plot_{current_time}.png"

    local_file_path = os.path.join(upload_folder, local_file_name)
    plt.savefig(local_file_path, format='png')
    plt.close()
    folder_name = "confusion_matrix"  # Replace with your desired folder_name
    # Upload the local file to S3
    s3_image_url = upload_generated_file_to_s3(local_file_path, folder_name)
    print("S3 Image URL:", s3_image_url)

    # Remove the local file after uploading
    os.remove(local_file_path)

    # Precision, recall, F1-score
    precision = precision_score(y_new, predicted_classes, average='weighted')
    recall = recall_score(y_new, predicted_classes, average='weighted')
    f1 = f1_score(y_new, predicted_classes, average='weighted')

    
        # Binarize the labels for multi-class ROC AUC
    y_new_binarized = label_binarize(y_new, classes=np.unique(y_new))
    n_classes = y_new_binarized.shape[1]

    # Compute ROC curve and ROC area for each class
    fpr = dict()
    tpr = dict()
    roc_auc = dict()

    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_new_binarized[:, i], predictions[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

     # Plot all ROC curves
    plt.figure(figsize=(10, 7))
    colors = plt.cm.tab10.colors  # Use a specific colormap, e.g., tab10
    for i, color in zip(range(n_classes), colors):
        plt.plot(fpr[i], tpr[i], color=color, lw=2, label=f'ROC curve of class {i} (area = {roc_auc[i]:.2f})')
    plt.plot([0, 1], [0, 1], 'k--', lw=2)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curves')
    plt.legend(loc='lower right')

    # Save the plot with current time in the "images_upload" folder
    upload_folder = "images_upload"
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    local_file_name = f"roc_curve_plot_{current_time}.png"
    local_file_path = os.path.join(upload_folder, local_file_name)
    plt.savefig(local_file_path, format='png')
    plt.close()

    # Upload the local file to S3
    roc_curve_s3_url = upload_generated_file_to_s3(local_file_path, "roc_curves")
    print("ROC Curve S3 URL:", roc_curve_s3_url)

    # Remove the local file after uploading
    os.remove(local_file_path)

    
    # Class distribution

    # Checking the distribution of the predicted classes
    # Define a mapping dictionary for class labels
    label_mapping = {
        0: "UP",
        1: "DOWN",
        2: "RIGHT",
        3: "LEFT"
    }

    # Checking the distribution of the predicted classes
    unique, counts = np.unique(predicted_classes, return_counts=True)
    class_distribution = {}

    print("Class Distribution in Predictions:")
    for key, value in zip(unique, counts):
        mapped_key = label_mapping[key] if key in label_mapping else f"Class {key}"
        # Convert value to int (if it's int64)
        value = int(value)
        class_distribution[mapped_key] = value
        print(f"Class {mapped_key}: {value} samples")

    # Now class_distribution dictionary contains the distribution of predicted classes
    print("Class Distribution Dictionary:", class_distribution)

    # Summary report
    summary_report = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "classification_report": report,
        "confusion_matrix_image_url": s3_image_url,  
        "roc_auc": roc_curve_s3_url,
        "class_distribution": class_distribution
    }

    is_success=save_summary_to_dynamodb(summary_report, 'Model_Prediction')
    print("=================Data save in db==========",is_success)
    # return summary_report
    return summary_report
