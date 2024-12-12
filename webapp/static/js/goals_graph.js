// goals_graph.js
// Ensure the DOM is loaded before rendering the graph
document.addEventListener('DOMContentLoaded', function () {
  // Data injected from Flask template (ensure it matches the variable used in Flask)

    JSON.parse(document.getElementById('goals-data').textContent)
    const goalsToday = JSON.parse(document.getElementById('goals-data').textContent);
        console.log(goalsToday)
        // Map the data to include the calculated pct_goal and remaining_pct (percentage of goal)
        const vegaData = goalsToday.map(entry => {
            const pctGoal = entry[3];
            // Validate pctGoal and set remainingPct accordingly
            const validPctGoal = isNaN(pctGoal) || pctGoal === Infinity || pctGoal === -Infinity ? 0 : pctGoal;
            // Ensure remainingPct is not negative, if pctGoal > 100, set remainingPct to 0
            const remainingPct = validPctGoal > 100 ? 0 : 100 - validPctGoal; // If goal exceeds 100%, remainingPct is 0
    
            return {
                nutrients: entry[0],  // Nutrient type (e.g., Calories, Carbs)
                calories: entry[1],    // Daily Calories -- actual meal values (calories - g, others - %)
                goals: entry[2],       // Goals (%)
                pct_goal: validPctGoal,  // Percentage of goal (meals % relative to user-defined goal)
                remaining_pct: remainingPct  // Remaining part of the goal
            };
        });
      
        // Function to generate and render the pie chart for each nutrient
        const renderGraphForNutrient = (nutrient) => {
            const nutrientData = vegaData.filter(entry => entry.nutrients === nutrient);
            // clean data
            const pieData = {
                values: [{
                    category: "Percent met to goal",
                    pct_goal: nutrientData[0].pct_goal,
                    "color": "rgb(40, 167, 69)"
                }, 
                {
                    category: "Remaining percent to goal",
                    pct_goal: nutrientData[0].remaining_pct,
                    "color": "rgb(155, 232, 173)"
                }]
            }

            // // odd concatenation
            // console.log('nutrientData CONCAT', nutrientData.concat(nutrientData.map(entry => ({
            //     pct_goal: entry.remaining_pct,
            // }))))
            // Create the Vega-Lite specification for the pie chart of the given nutrient
            const vegaSpec = {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "width": 275,
                "height": 400,     
                "description": `${nutrient} Nutrition Goal`,  
                "background": "#f9f9f9",
                "data": pieData,
                "config": {
                    "style": {
                        "cell": {
                            "stroke": "transparent"
                        }
                    }
                },
                "mark":  {
                    "type": "arc",  // Use the "arc" mark to create a pie chart
                    "innerRadius": 50, 
                    "stroke": null
                }, 
                "encoding": {
                    "theta": {
                        "field": "pct_goal",  // Use pct_goal for the angular position of the slice
                        "type": "quantitative",
                        "stack": true
                    },
                    "color": {
                        "field": "color", "type": "nominal", "legend": null, "scale": {
                            "scheme": "greens"
                        }
                    },
                    "tooltip": [
                        {
                            field: "category",
                            title: "category",
                        },
                        // {
                        //     "field": "pct_goal", 
                        //     "title": "Goal %", 
                        //     "format": ".2f"  // Display as a float with 2 decimal places (e.g., 50.00)
                        // },
                        {
                            "field": "pct_goal", 
                            "title": "Goal %", 
                            "format": ".2f",  // Format number to 2 decimal places
                            "type": "quantitative",  // Ensure it's treated as a number
                            "expression": "datum.category + '%'"  // Append '%' sign to the value
                        },
                    ]
                }, 
                "title": { 
                    "text": `${nutrient}\nis ${nutrientData[0].pct_goal.toFixed(0)}% to Your Goal`, // Add the nutrient name at the top of the chart
                    "anchor": "middle", 
                    "fontSize": 14, 
                    "font": "Righteous",
                    "dy": -10 //Adjust the vertical position of the title
                }
            };
        
            console.log('vegaSpec.data', vegaSpec.data.values)
            // Render the pie chart for this nutrient in the respective div
            vegaEmbed(`#${nutrient}-graph`, vegaSpec, {renderer: "svg", actions: false})
                .then(() => console.log(`${nutrient} pie chart rendered successfully.`))
                .catch(console.error);
        };
      
        
    if (goalsToday.length > 0) {
        document.getElementById('graphs').style.display = 'block'
        // List of all nutrients
        const nutrientsList = ['Calories', 'Carbs', 'Fats', 'Proteins'];
      
        // Render pie charts for each nutrient
        nutrientsList.forEach(nutrient => {
            renderGraphForNutrient(nutrient);

        });
    } else {
        document.getElementById('selection').style.display = 'block'
        console.warn('Returned no goals and/or food for the day')
    }
}); 