import argparse
import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
import joblib
from azureml.core.run import Run
from azureml.data.dataset_factory import TabularDatasetFactory

# Load the dataset
data_loc = "https://automlsamplenotebookdata.blob.core.windows.net/automl-sample-notebook-data/bankmarketing_train.csv"
ds = TabularDatasetFactory.from_delimited_files(data_loc)

# Initialize Azure ML run context
run = Run.get_context()

def clean_data(data):
    """
    Clean and preprocess the data.
    
    Args:
    data (TabularDataset): The dataset to be cleaned and preprocessed.
    
    Returns:
    pd.DataFrame, pd.Series: The feature dataframe and target series.
    """
    months = {"jan":1, "feb":2, "mar":3, "apr":4, "may":5, "jun":6, "jul":7, "aug":8, "sep":9, "oct":10, "nov":11, "dec":12}
    weekdays = {"mon":1, "tue":2, "wed":3, "thu":4, "fri":5, "sat":6, "sun":7}

    x_df = data.to_pandas_dataframe().dropna()
    
    # One hot encoding for 'job' column
    x_df = pd.get_dummies(x_df, columns=['job'], prefix='job')
    
    # Binary encoding for some categorical columns
    x_df["marital"] = x_df.marital.apply(lambda s: 1 if s == "married" else 0)
    x_df["default"] = x_df.default.apply(lambda s: 1 if s == "yes" else 0)
    x_df["housing"] = x_df.housing.apply(lambda s: 1 if s == "yes" else 0)
    x_df["loan"] = x_df.loan.apply(lambda s: 1 if s == "yes" else 0)
    
    # One hot encoding for 'contact' column
    x_df = pd.get_dummies(x_df, columns=['contact'], prefix='contact')
    
    # One hot encoding for 'education' column
    x_df = pd.get_dummies(x_df, columns=['education'], prefix='education')
    
    # Mapping 'month' and 'day_of_week' columns
    x_df["month"] = x_df.month.map(months)
    x_df["day_of_week"] = x_df.day_of_week.map(weekdays)
    
    # Binary encoding for 'poutcome' column
    x_df["poutcome"] = x_df.poutcome.apply(lambda s: 1 if s == "success" else 0)

    # Extract target column 'y' and encode it
    y_df = x_df.pop("y").apply(lambda s: 1 if s == "yes" else 0)

    return x_df, y_df

# Clean the data
x, y = clean_data(ds)

# Split the data into train and test sets
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=123)

def main():
    # Add arguments to the script
    parser = argparse.ArgumentParser()

    parser.add_argument('--C', type=float, default=1.0, help="Inverse of regularization strength. Smaller values cause stronger regularization")
    parser.add_argument('--max_iter', type=int, default=100, help="Maximum number of iterations to converge")

    args = parser.parse_args()

    run.log("Regularization Strength:", np.float(args.C))
    run.log("Max iterations:", np.int(args.max_iter))

    # Train the model
    model = LogisticRegression(C=args.C, max_iter=args.max_iter, random_state=123).fit(x_train, y_train)

    # Evaluate the model
    accuracy = model.score(x_test, y_test)
    run.log("Accuracy", np.float(accuracy))

    # Save the model
    os.makedirs('outputs', exist_ok=True)
    joblib.dump(model, f'outputs/hyperDrive_{args.C}_{args.max_iter}.pkl')

if __name__ == '__main__':
    main()
