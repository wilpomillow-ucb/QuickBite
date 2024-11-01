let selectedMealName = null;
let uploadedImagePath = '';
let selectedPrediction = null;

// Mapping NTR codes to nutrient names and units
const nutrientMapping = {
    'SUGAR.added': { name: 'Added sugar', unit: 'g' },
    CA: { name: 'Calcium, Ca', unit: 'mg' },
    'CHOCDF.net': { name: '   Carbohydrate (net)', unit: 'g' },
    CHOCDF: { name: 'Carbohydrate, by difference', unit: 'g' },
    CHOLE: { name: 'Cholesterol', unit: 'mg' },
    ENERC_KCAL: { name: 'Energy', unit: 'kcal' },
    FAMS: { name: '   Fatty acids, total monounsaturated', unit: 'g' },
    FAPU: { name: '   Fatty acids, total polyunsaturated', unit: 'g' },
    FASAT: { name: '   Fatty acids, total saturated', unit: 'g' },
    FATRN: { name: '   Fatty acids, total trans', unit: 'g' },
    FIBTG: { name: 'Fiber, total dietary', unit: 'g' },
    FOLDFE: { name: 'Folate, DFE', unit: 'µg' },
    FOLFD: { name: '   Folate, food', unit: 'µg' },
    FOLAC: { name: '   Folic acid', unit: 'µg' },
    FE: { name: 'Iron, Fe', unit: 'mg' },
    MG: { name: 'Magnesium', unit: 'mg' },
    NIA: { name: 'Niacin', unit: 'mg' },
    P: { name: 'Phosphorus, P', unit: 'mg' },
    K: { name: 'Potassium, K', unit: 'mg' },
    PROCNT: { name: 'Protein', unit: 'g' },
    RIBF: { name: 'Riboflavin', unit: 'mg' },
    NA: { name: 'Sodium, Na', unit: 'mg' },
    'Sugar.alcohol': { name: 'Sugar alcohols', unit: 'g' },
    SUGAR: { name: 'Sugars, total', unit: 'g' },
    THIA: { name: 'Thiamin', unit: 'mg' },
    FAT: { name: 'Total lipid (fat)', unit: 'g' },
    VITA_RAE: { name: 'Vitamin A, RAE', unit: 'µg' },
    VITB12: { name: 'Vitamin B-12', unit: 'µg' },
    VITB6A: { name: 'Vitamin B-6', unit: 'mg' },
    VITC: { name: 'Vitamin C, total ascorbic acid', unit: 'mg' },
    VITD: { name: 'Vitamin D (D2 + D3)', unit: 'µg' },
    TOCPHA: { name: 'Vitamin E (alpha-tocopherol)', unit: 'mg' },
    VITK1: { name: 'Vitamin K (phylloquinone)', unit: 'µg' },
    WATER: { name: 'Water', unit: 'g' },
    ZN: { name: 'Zinc, Zn', unit: 'mg' },
};

document.addEventListener('DOMContentLoaded', function () {
    const titleRefresh = document.getElementById('title-refresh');
    if (titleRefresh) {
        titleRefresh.addEventListener('click', function () {
            window.location.reload();
        });
    } else {
        console.error('Element with ID "title-refresh" not found.');
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const mealList = document.querySelector('.meal-list ul');
    const popup = document.getElementById('popup');
    const popupOverlay = document.querySelector('.popup-overlay');
    const closePopupBtns = document.querySelectorAll('.close');

    if (mealList) {
        mealList.addEventListener('click', handleMealClick);
    }

    closePopupBtns.forEach((btn) => btn.addEventListener('click', closePopup));
    popupOverlay.addEventListener('click', handleOverlayClick);
});

function closePopup() {
    popup.style.display = 'none';
    popupOverlay.style.visibility = 'hidden';
    popupOverlay.style.opacity = '0';
}

function handleOverlayClick(event) {
    if (event.target === popupOverlay) closePopup();
}

const mealList = document.querySelector('.meal-list ul');
const popup = document.getElementById('popup');
const popupMessage = document.getElementById('popup-message');
const popupOverlay = document.querySelector('.popup-overlay');
const closePopupBtn = document.querySelectorAll('.close');

document.addEventListener('click', function (event) {
    const target = event.target;

    if (target.classList.contains('close-popup')) {
        closePopup();
    }

    if (target.classList.contains('popup-overlay')) {
        closePopup();
    }
});

closePopupBtns.forEach((btn) => btn.addEventListener('click', closePopup));
popupOverlay.addEventListener('click', handleOverlayClick);

function toTitleCase(str) {
    return str.toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
}

function generateNutritionalRows(nutrients) {
    return Object.entries(nutrients)
        .map(([key, value]) => {
            const nutrient = nutrientMapping[key] || { name: key, unit: '' };
            const amount = value.quantity ? value.quantity.toFixed(2) : 0;
            const unit = value.unit || '';
            const nutrientName = nutrient.name.replace(/^ +/g, (match) => '&nbsp;'.repeat(match.length));

            return `
            <tr>
                <td>${nutrientName}</td>
                <td>${amount} ${unit}</td>
            </tr>
        `;
        })
        .join('');
}

let isTableVisible = false;

function toggleNutritionalTable() {
    const table = document.getElementById('nutritional-facts-table');
    const triangleIcon = document.getElementById('toggle-icon');

    if (table.style.display === 'none' || table.style.display === '') {
        table.style.display = 'block';
        triangleIcon.classList.add('rotate-up');
    } else {
        table.style.display = 'none';
        triangleIcon.classList.remove('rotate-up');
    }
}

function triggerFileUpload() {
    document.getElementById('fileInput').click();
}

function uploadImage() {
    const button = document.querySelector('.add-diary-button');
    button.innerHTML = 'Analysing...';
    button.disabled = true;
    button.style.cursor = 'default';

    const formData = new FormData(document.getElementById('uploadForm'));

    fetch('/upload', {
        method: 'POST',
        body: formData,
    })
        .then((response) => response.json())
        .then((data) => {
            uploadedImagePath = data.image_path;
            console.log('Image uploaded:', uploadedImagePath);
            showPopup(uploadedImagePath, data.predictions);

            button.innerHTML = 'Analysis Complete';
            button.disabled = false;
            button.style.cursor = 'pointer';
            document.getElementById('fileInput').value = '';
        })
        .catch((error) => {
            console.error('Error uploading image:', error);
            button.innerHTML = '+ Diary Entry';
            button.disabled = false;
            button.style.cursor = 'pointer';
        });
}

function showPopup(imagePath, predictions) {
    uploadedImagePath = imagePath;
    const popupHtml = `
        <div class="popup-overlay" id="popup-overlay">
            <div class="popup-content">
                <button class="close-popup" onclick="closePopup()">&#10006;</button>
                <img src="/${uploadedImagePath}" alt="Uploaded Image" class="popup-image">
                <div class="prediction-question">Which best describes your meal?</div>
                <div class="prediction-buttons">
                    ${predictions
                        .map(
                            (prediction, index) => `
                        <button class="prediction-button" onclick="submitPrediction('${prediction}')">${prediction}</button>
                    `
                        )
                        .join('')}
                </div>
                <div class="custom-input-container">
                    <label for="customMeal">Or type your own description:</label>
                    <input type="text" id="customMeal" name="customMeal" placeholder="Describe your meal" oninput="updateSubmitButton()">
                </div>
                <button class="submit-button" id="submitButton" onclick="submitQuery()">Submit</button>
                <div class="result-container" id="resultContainer" style="display: none;"></div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', popupHtml);
}

function closePopup() {
    const popupOverlay = document.getElementById('popup-overlay');
    if (popupOverlay) {
        popupOverlay.remove();
    }
    const button = document.querySelector('.add-diary-button');
    button.disabled = false;
    button.innerHTML = '+ Diary Entry';
}

function selectPrediction(prediction) {
    selectedMealName = prediction;
    const selectedMealName = prediction;
    console.log('Selected meal name (select prediction):', selectedMealName);
    document.querySelector('.prediction-question').style.display = 'none';
}

function submitPrediction(prediction) {
    document.querySelector('.prediction-question').style.display = 'none';
    selectedMealName = prediction;
    console.log('Selected meal name (submit prediction):', selectedMealName);
    displayLoadingState();
    fetchRecipes(selectedMealName, uploadedImagePath);
}

async function submitQuery() {
    document.querySelector('.prediction-question').style.display = 'none';
    const customMeal = document.getElementById('customMeal').value.trim();

    if (customMeal) {
        selectedMealName = customMeal;
    }

    if (!customMeal && !selectedMealName) {
        shakeButton(document.getElementById('submitButton'));
        return;
    }
    console.log('Selected meal name:', selectedMealName);
    displayLoadingState();
    fetchRecipes(selectedMealName, uploadedImagePath);
}

document.querySelectorAll('.prediction-button').forEach((button) => {
    button.addEventListener('click', function () {
        submitPrediction(this.innerText);
    });
});

function displayLoadingState() {
    const predictionButtons = document.querySelector('.prediction-buttons');
    const customInputContainer = document.querySelector('.custom-input-container');
    const submitButton = document.querySelector('.submit-button');
    const resultContainer = document.getElementById('resultContainer');

    if (predictionButtons) predictionButtons.style.display = 'none';
    if (customInputContainer) customInputContainer.style.display = 'none';
    if (submitButton) submitButton.style.display = 'none';

    resultContainer.style.display = 'block';
    resultContainer.innerHTML = `<p>Loading...</p>`;
}

function updateSubmitButton() {
    const customMeal = document.getElementById('customMeal').value.trim();
    const submitButton = document.getElementById('submitButton');

    if (customMeal || selectedPrediction) {
        submitButton.disabled = false;
        submitButton.classList.remove('grey');
        submitButton.classList.add('green');
    } else {
        submitButton.disabled = true;
        submitButton.classList.remove('green');
        submitButton.classList.add('grey');
    }
}

function shakeButton(button) {
    button.classList.add('shake', 'red');
    setTimeout(() => {
        button.classList.remove('shake', 'red');
    }, 500);
}

function fetchRecipes(foodQuery, imagePath) {
    const API_KEY = '3a33117cb5302829fce64c70db156de9';
    const APP_ID = '2a940906';

    fetch(`https://api.edamam.com/api/recipes/v2?type=public&q=${foodQuery}&app_id=${APP_ID}&app_key=${API_KEY}`)
        .then((response) => response.json())
        .then((data) => {
            const topRecipes = data.hits.slice(0, 5);
            const bestMatch = findBestMatch(foodQuery, topRecipes);
            displayNutritionalInfo(bestMatch, imagePath);
        })
        .catch((error) => {
            console.error('Error fetching recipes:', error);
            document.getElementById(
                'resultContainer'
            ).innerHTML = `<p>Error loading results. Please try again later.</p>`;
        });
}

function findBestMatch(foodQuery, recipes) {
    let highestSimilarity = 0;
    let bestMatch = null;

    recipes.forEach((hit) => {
        const recipe = hit.recipe;
        const similarity = calculateStringSimilarity(foodQuery, recipe.label);

        if (similarity > highestSimilarity) {
            highestSimilarity = similarity;
            bestMatch = recipe;
        }
    });

    return bestMatch;
}

function calculateStringSimilarity(str1, str2) {
    str1 = str1.toLowerCase();
    str2 = str2.toLowerCase();

    const distance = levenshteinDistance(str1, str2);
    const maxLength = Math.max(str1.length, str2.length);
    return 1 - distance / maxLength;
}

function levenshteinDistance(a, b) {
    const matrix = [];

    for (let i = 0; i <= b.length; i++) {
        matrix[i] = [i];
    }

    for (let j = 0; j <= a.length; j++) {
        matrix[0][j] = j;
    }

    for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
            if (b.charAt(i - 1) === a.charAt(j - 1)) {
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(
                    matrix[i - 1][j - 1] + 1, // Substitution
                    matrix[i][j - 1] + 1, // Insertion
                    matrix[i - 1][j] + 1 // Deletion
                );
            }
        }
    }

    return matrix[b.length][a.length];
}

// Function to display the nutritional information
function displayNutritionalInfo(recipe, uploadedImagePath) {
    const resultContainer = document.getElementById('resultContainer');
    resultContainer.style.display = 'block';

    const totalWeight = recipe.totalWeight ? recipe.totalWeight.toFixed(2) : 'N/A';
    const originalCalories = recipe.calories;
    const originalCarbs = recipe.totalNutrients.CHOCDF.quantity;
    const originalFat = recipe.totalNutrients.FAT.quantity;
    const originalProtein = recipe.totalNutrients.PROCNT.quantity;
    const originalSUGAR_added_g = recipe.totalNutrients.SUGAR['added']
        ? recipe.totalNutrients.SUGAR['added'].quantity
        : 0;
    const originalCA_mg = recipe.totalNutrients.CA.quantity;
    const originalCHOCDF_net_g = recipe.totalNutrients.CHOCDF['net'] ? recipe.totalNutrients.CHOCDF['net'].quantity : 0;
    const originalCHOCDF_g = recipe.totalNutrients.CHOCDF.quantity;
    const originalCHOLE_mg = recipe.totalNutrients.CHOLE.quantity;
    const originalFAMS_g = recipe.totalNutrients.FAMS.quantity;
    const originalFAPU_g = recipe.totalNutrients.FAPU.quantity;
    const originalFASAT_g = recipe.totalNutrients.FASAT.quantity;
    const originalFATRN_g = recipe.totalNutrients.FATRN ? recipe.totalNutrients.FATRN.quantity : 0;
    const originalFIBTG_g = recipe.totalNutrients.FIBTG.quantity;
    const originalFOLDFE_microg = recipe.totalNutrients.FOLDFE.quantity;
    const originalFOLFD_microg = recipe.totalNutrients.FOLFD.quantity;
    const originalFOLAC_microg = recipe.totalNutrients.FOLAC.quantity;
    const originalFE_mg = recipe.totalNutrients.FE.quantity;
    const originalMG_mg = recipe.totalNutrients.MG.quantity;
    const originalNIA_mg = recipe.totalNutrients.NIA.quantity;
    const originalP_mg = recipe.totalNutrients.P.quantity;
    const originalK_mg = recipe.totalNutrients.K.quantity;
    const originalRIBF_mg = recipe.totalNutrients.RIBF.quantity;
    const originalNA_mg = recipe.totalNutrients.NA.quantity;
    const originalSUGAR_ALCOHOL_g = 0; // recipe.totalNutrients.Sugar['alcohol'] ? recipe.totalNutrients.SUGAR['alcohol'].quantity : 0;
    const originalSUGAR_g = recipe.totalNutrients.SUGAR.quantity;
    const originalTHIA_mg = recipe.totalNutrients.THIA.quantity;
    const originalVITA_RAE_microg = recipe.totalNutrients.VITA_RAE.quantity;
    const originalVITB12_microg = recipe.totalNutrients.VITB12.quantity;
    const originalVITB6A_mg = recipe.totalNutrients.VITB6A.quantity;
    const originalVITC_mg = recipe.totalNutrients.VITC.quantity;
    const originalVITD_microg = recipe.totalNutrients.VITD.quantity;
    const originalTOCPHA_mg = recipe.totalNutrients.TOCPHA.quantity;
    const originalVITK_microg = recipe.totalNutrients.VITK1.quantity;
    const originalWATER_g = recipe.totalNutrients.WATER.quantity;
    const originalZN_mg = recipe.totalNutrients.ZN.quantity;
    console.log(recipe);

    // Add consts for diet labels, health labels, and cautions
    const combinedLabels = [...new Set([...recipe.dietLabels, ...recipe.healthLabels, ...recipe.cautions])];
    const labelPills = combinedLabels
        .map((label) => {
            return `<span class="pill">${label}</span>`;
        })
        .join('');

    const ingredients = recipe.ingredients
        .map((ingredient) => `<span class="pill">${toTitleCase(ingredient.food)}</span>`)
        .join('');
    console.log(ingredients);

    // Display the recipe's nutritional information and add servings input and "Add to Diary" button
    resultContainer.innerHTML = `
        <div class="nutrition-grid">
            <div class="nutrition-item">
                <span class="quantity-large" id="calories-value">${originalCalories.toFixed(
                    2
                )}</span><span class="unit-small">kcal</span>
                <p>Calories</p>
            </div>
            <div class="nutrition-item">
                <span class="quantity-large" id="carbs-value">${originalCarbs.toFixed(
                    2
                )}</span><span class="unit-small">g</span>
                <p>Carbs</p>
            </div>
            <div class="nutrition-item">
                <span class="quantity-large" id="fat-value">${originalFat.toFixed(
                    2
                )}</span><span class="unit-small">g</span>
                <p>Fat</p>
            </div>
            <div class="nutrition-item">
                <span class="quantity-large" id="protein-value">${originalProtein.toFixed(
                    2
                )}</span><span class="unit-small">g</span>
                <p>Protein</p>
            </div>
        </div>

        <h3>Labels</h3>
        <div class="scrollable-container">
            ${labelPills}
        </div>

        <h3>Potential Ingredients</h3>
        <div class="scrollable-container">
            ${ingredients}
        </div>
    
        <h3 class="info-icon" onclick="toggleNutritionalTable()">
        <span id="toggle-icon" class="triangle">&#9660;</span>

        More Nutritional Facts
        <sup style="font-size: 0.6em;" class="tooltip-icon">&#9432;
            <span class="tooltip-text">Disclaimer: Indicative of Single Serving</span>
        </sup>
            </h3>

        <div id="nutritional-facts-table" class="hidden-table">
            <table class="auto-width-table">
                <thead>
                    <tr>
                        <th>Nutrient</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                    ${generateNutritionalRows(recipe.totalNutrients)}
                </tbody>
            </table>
        </div>

        <label for="servings" style="margin-top: 5px; display: inline-block;"># of Servings</label>
        <input type="number" id="servings" name="servings" min="1" value="1" style="width: 100px; margin-top: 10px; padding: 5px;">
        <label for="servings" style="margin-top: 5px; display: inline-block;">based on ${totalWeight}g</label>

        <button class="add-to-diary-btn">Add to Diary</button>
    `;

    document.getElementById('servings').addEventListener('input', function () {
        let servings = parseFloat(this.value) || 1;

        if (servings < 0) {
            servings = 1; // Reset to 1 if the input is less than 1
            this.value = servings;
        }

        document.getElementById('calories-value').innerText = (originalCalories * servings).toFixed(2);
        document.getElementById('carbs-value').innerText = (originalCarbs * servings).toFixed(2);
        document.getElementById('fat-value').innerText = (originalFat * servings).toFixed(2);
        document.getElementById('protein-value').innerText = (originalProtein * servings).toFixed(2);
    });

    document.querySelector('.add-to-diary-btn').addEventListener('click', async function () {
        console.log('Add to Diary button clicked!');

        const button = this;
        const servings = parseFloat(document.getElementById('servings').value) || 1;
        const mealName = selectedMealName || document.getElementById('customMeal').value.trim();

        console.log('Submitting:', mealName);

        // Nutritional values (multiplied by the number of servings)
        const nutritionalData = {
            SUGAR_added_g: (originalSUGAR_added_g * servings).toFixed(2),
            CA_mg: (originalCA_mg * servings).toFixed(2),
            CHOCDF_net_g: (originalCHOCDF_net_g * servings).toFixed(2),
            CHOCDF_g: (originalCHOCDF_g * servings).toFixed(2),
            CHOLE_mg: (originalCHOLE_mg * servings).toFixed(2),
            ENERC_KCAL_kcal: (originalCalories * servings).toFixed(2),
            FAMS_g: (originalFAMS_g * servings).toFixed(2),
            FAPU_g: (originalFAPU_g * servings).toFixed(2),
            FASAT_g: (originalFASAT_g * servings).toFixed(2),
            FATRN_g: (originalFATRN_g * servings).toFixed(2),
            FIBTG_g: (originalFIBTG_g * servings).toFixed(2),
            FOLDFE_microg: (originalFOLDFE_microg * servings).toFixed(2),
            FOLFD_microg: (originalFOLFD_microg * servings).toFixed(2),
            FOLAC_microg: (originalFOLAC_microg * servings).toFixed(2),
            FE_mg: (originalFE_mg * servings).toFixed(2),
            MG_mg: (originalMG_mg * servings).toFixed(2),
            NIA_mg: (originalNIA_mg * servings).toFixed(2),
            P_mg: (originalP_mg * servings).toFixed(2),
            K_mg: (originalK_mg * servings).toFixed(2),
            PROCNT_g: (originalProtein * servings).toFixed(2),
            RIBF_mg: (originalRIBF_mg * servings).toFixed(2),
            NA_mg: (originalNA_mg * servings).toFixed(2),
            SUGAR_ALCOHOL_g: (originalSUGAR_ALCOHOL_g * servings).toFixed(2),
            SUGAR_g: (originalSUGAR_g * servings).toFixed(2),
            THIA_mg: (originalTHIA_mg * servings).toFixed(2),
            FAT_g: (originalFat * servings).toFixed(2),
            VITA_RAE_microg: (originalVITA_RAE_microg * servings).toFixed(2),
            VITB12_microg: (originalVITB12_microg * servings).toFixed(2),
            VITB6A_mg: (originalVITB6A_mg * servings).toFixed(2),
            VITC_mg: (originalVITC_mg * servings).toFixed(2),
            VITD_microg: (originalVITD_microg * servings).toFixed(2),
            TOCPHA_mg: (originalTOCPHA_mg * servings).toFixed(2),
            VITK_microg: (originalVITK_microg * servings).toFixed(2),
            WATER_g: (originalWATER_g * servings).toFixed(2),
            ZN_mg: (originalZN_mg * servings).toFixed(2),
        };

        button.disabled = true;
        button.style.backgroundColor = 'grey';
        button.style.cursor = 'not-allowed';

        console.log('Preparing to send the following data to the backend:', {
            meal_name: selectedMealName,
            serving_count: servings,
            path_to_image: uploadedImagePath,
            nutritional_data: nutritionalData,
        });

        try {
            const response = await fetch('/add_to_diary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    meal_name: mealName,
                    serving_count: servings,
                    path_to_image: uploadedImagePath,
                    nutritional_data: nutritionalData,
                }),
            });

            const data = await response.json();
            if (data.status === 'success') {
                closePopup();
                window.location.reload();
            } else {
                console.error('Error from backend:', data.message);
                alert('There was an error adding the meal. Please try again.');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            alert('There was an error adding the meal. Please try again.');
        }
    });
}

function closePopup() {
    const popupOverlay = document.getElementById('popup-overlay');
    if (popupOverlay) {
        popupOverlay.remove();
        console.log('Pop-up closed.');
    }
}

popupOverlay.addEventListener('click', function (event) {
    if (event.target === popupOverlay) {
        closePopup();
    }
});

async function fetchMealImagePath(mealId) {
    console.log('Fetching image path for meal:', mealId);
    const response = await fetch(`/get_image_path?meal_id=${mealId}`);
    const data = await response.json();
    if (data.status === 'success') {
        uploadedImagePath = data.image_path;
        return data.image_path;
    } else {
        throw new Error(data.message || 'Image path not found');
    }
}

function showMealPopup(imagePath, mealName, mealInfo) {
    uploadedImagePath = imagePath;
    const existingPopup = document.getElementById('popup-overlay');
    if (existingPopup) existingPopup.remove();
    const popupHtml = `
        <div class="popup-overlay" id="popup-overlay">
            <div class="popup-content">
                <button class="close-popup" onclick="closePopup()">&#10006;</button>
                <h2>${mealName}</h2>
                <img src="/${uploadedImagePath}" alt="Meal Image" class="popup-image">
                <p>${mealInfo}</p>
                <button class="share-button" onclick"shareMeal()">Share</button>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', popupHtml);
    console.log('Path Confirmed:', uploadedImagePath);
}

mealList.addEventListener('click', handleMealClick);

function handleMealClick(event) {
    const clickedMeal = event.target.closest('li');
    if (!clickedMeal) return;

    const mealId = clickedMeal.dataset.mealId;
    const mealName = clickedMeal.querySelector('.meal-name').textContent;
    const mealInfo = clickedMeal.querySelector('.meal-info').textContent;

    logMealDetails(mealName, mealInfo);
    const popupOverlay = document.querySelector('.popup-overlay');

    fetchMealImagePath(mealId)
        .then((imagePath) => {
            console.log('Fetched Image Path:', imagePath);
            showMealPopup(imagePath, mealName, mealInfo);
        })
        .catch((error) => console.error('Error fetching image path:', error));
}

function getMealName(mealElement) {
    return mealElement.querySelector('.meal-name').textContent;
}

function getMealInfo(mealElement) {
    return mealElement.querySelector('.meal-info').textContent;
}

function logMealDetails(mealName, mealInfo) {
    console.log(`Meal: ${mealName}`);
    console.log(`Details: ${mealInfo}`);
}

function shareMeal() {
    alert('Share Meal function is pending implementation.');
    console.log('Share button clicked!');
}
