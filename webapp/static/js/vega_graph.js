// vega_graph.js

// Ensure the DOM is loaded before rendering the graph
document.addEventListener('DOMContentLoaded', function () {
  // Data injected from Flask template (ensure it matches the variable used in Flask)

  JSON.parse(document.getElementById('meals-data').textContent)
  const mealsLast7Days = JSON.parse(document.getElementById('meals-data').textContent);

  const vegaData = mealsLast7Days.map(entry => ({
      day: entry[0],  // Date (YYYY-MM-DD)
      calories: entry[1],  // Calories
      protein: entry[2], // Protein
      carbs: entry[3], // Carbs 
      fat: entry[4] // Fat
  }));

  // Vega specification for the bar graph
  const vegaSpec = {
      "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
      "width": 1000,
      "height": 300,     
      "description": "Nutrition data over the last 7 days.",
      "params": [
        {
            "name": "Nutrition",
            "value": "calories",
            "bind": {
                "input": "select",
                "options": ["calories", "protein", "carbs", "fat"]
            }
        }
    ],
    "data": {
        "values": vegaData
    },
    "transform": [
        {
            "calculate": "datum[Nutrition]",
            "as": "nutritionValue"
        }
    ],
      "mark": "bar",
      "config": {
        "background": "#f9f9f9", 
        "legend": {
            "labelFont":"Nunito", 
            "titleFont": "Righteous", 
            "titleFontSize": 12
        }
      }, 
      "encoding": {
          "x": {
              "field": "day",
              "type": "ordinal",
              "axis": {
                "title": "Day",
                "labelFont": "Nunito",
                "titleFont": "Righteous",
                "titleFontSize": 14
              }
          },
          "y": {
            "field": "nutritionValue",
            "type": "quantitative",
            "axis": {
                "title": {"signal": "Nutrition"},
                "labelFont": "Nunito",
                "titleFont": "Righteous",
                "titleFontSize": 14,
                "labels": false
            }
        },
        "color": {
            "field": "nutritionValue",
            "type": "quantitative",
            "scale": { "scheme": "greens" },
            "legend": {
                "title": {"signal": "Nutrition"},
                "labelFont": "Nunito",
                "titleFont": "Righteous",
                "titleFontSize": 12
            }
        },
        "tooltip": {
            "field": "nutritionValue",
            "type": "quantitative"
        }
    }
  };

  // Render the Vega graph in the #nutrition-graph-7-day div
  vegaEmbed('#nutrition-graph-7-day', vegaSpec, {renderer: "svg", actions: false})
      .then(() => console.log("Vega graph rendered successfully."))
      .catch(console.error);
});
