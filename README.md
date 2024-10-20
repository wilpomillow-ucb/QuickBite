# QuickBite

## Repo Structure

* `webapp/` - Contains the webapp code
* `notebooks/` - Contains the notebooks used for data analysis
* `data/` - Empty directory where the training data should be put in for the notebooks to work. Small csv files can be included in the repo, but large image files should not.


## Running the web app locally

To run QuickBite locally, download the repo and run `app.py`.
This will be hosted on your local which can be accessed via your web browser at HTTP://127.0.0.1:5000 

Requirements for the local environment:
|library         |Version                        |Purpose                      |
|----------------|-------------------------------|-----------------------------|
|flask           |Latest                         |Python web framework library |
|flask_login     |Latest                         |Python web authentication    |
|bcrypt          |Latest                         |Blowfish encryption          |
|email_validator |Latest                         |String validation for signup |
|sqlite3         |Latest                         |Database management          |
|datetime        |Latest                         |Datetime management          |
|inference_sdk   |Latest                         |API Inference to ML models   |
