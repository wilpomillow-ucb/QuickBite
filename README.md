# QuickBite


## About QuickBite
Regularly measuring calorie intake presents significant challenges for the average consumer due to several factors. Accurately assessing portion sizes, interpreting nutritional labels, and accounting for the composition of meals, particularly in restaurant settings or with homemade recipes, can be complex and prone to error. Many food items lack readily accessible or clear calorie information, making estimation difficult and often leading to inaccuracies.  Furthermore, consistently monitoring and recording food consumption requires substantial effort and attention, which can become mentally taxing and time-intensive. While digital tools and applications may assist with tracking, they still demand active user input and adherence, contributing to the perceived burden of routine calorie monitoring. The failure to accurately identify food contents can have significant and far-reaching consequences, particularly for individuals with specific dietary needs, allergies, or health-related restrictions. For those with food allergies, a lack of ingredient transparency can result in severe and potentially life-threatening reactions, such as anaphylaxis, when allergens like nuts, shellfish, or gluten are unknowingly consumed.
    
Individuals managing health conditions, such as diabetes or hypertension, may inadvertently consume harmful quantities of sugar, sodium, or fats, thereby worsening their health outcomes. Moreover, individuals adhering to dietary restrictions for religious reasons (e.g., halal or kosher) or ethical choices (e.g., veganism or vegetarianism) may unknowingly violate their nutritional principles due to hidden or unclear ingredients, leading to personal, ethical, or religious distress. The absence of clear labeling or accurate ingredient information can further result in negative long-term health effects, such as poor nutrition or the development of chronic conditions, as consumers are unable to make informed choices about the nutritional quality of their food. Thus, transparency in food labeling is essential for ensuring public safety, respecting dietary preferences, and promoting overall health.

## Repo Structure

* `webapp/` - Contains the webapp code
* `notebooks/` - Contains the notebooks used for data analysis
* `data/` - Empty directory where the training data should be put in for the notebooks to work. Small CSV files can be included in the repo, but large image files should not.

## Running the Web App Locally

To run QuickBite locally follow these steps

* Clone the repo
* Install the dependencies (see below)
    * Note: some dependencies are missing from the list below, please install them as needed
* Create a .env file and fill in the environment variables as shown in the .env.example file
* Download the deit model and move it to `data/models/deit_model.pth`
* Run `app.py`.
* Visit http://127.0.0.1:5000 in your browser.

Requirements for the environment:
|Library         |Version                        |Purpose                      |
|----------------|-------------------------------|-----------------------------|
|flask           |^3.0.3                         |Python web framework library |
|flask_login     |^0.6.3                         |Python web authentication    |
|bcrypt          |^4.2.0                         |Blowfish encryption          |
|email_validator |^2.2.0                         |String validation for signup |
|sqlite3         |Latest                         |Database management          |
|datetime        |Latest                         |Datetime management          |
|inference_sdk   |^0.21.1                        |API Inference to ML models   |

### Required API Registration
API Keys will be required to connect to external APIs:

|Service         |Reference                                                                                             |
|----------------|------------------------------------------------------------------------------------------------------|
|Edamam          |[Recipe Endpoint](https://developer.edamam.com/edamam-recipe-api)                                     |
|Roboflow        |[Classification Endpoint](https://docs.roboflow.com/deploy/hosted-api/custom-models/classification)   |
