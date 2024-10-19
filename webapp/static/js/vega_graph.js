// vega_graph.js

// Ensure the DOM is loaded before rendering the graph
document.addEventListener('DOMContentLoaded', function () {
  // Data injected from Flask template (ensure it matches the variable used in Flask)
  const mealsLast7Days = JSON.parse(document.getElementById('meals-data').textContent);

  const vegaData = mealsLast7Days.map(entry => ({
      day: entry[0],  // Date (YYYY-MM-DD)
      calories: entry[1]  // Calories
  }));

  // Vega specification for the bar graph
  const vegaSpec = {
      "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
      "description": "Calories consumed over the last 7 days.",
      "data": {
          "values": vegaData
      },
      "mark": "bar",
      "encoding": {
          "x": {
              "field": "day",
              "type": "ordinal",
              "axis": { "title": "Day" }
          },
          "y": {
              "field": "calories",
              "type": "quantitative",
              "axis": { "title": "Calories (kcal)" }
          },
          "color": {
              "field": "calories",
              "type": "quantitative",
              "scale": { "scheme": "blues" }
          }
      }
  };

  // Render the Vega graph in the #nutrition-graph-7-day div
  vegaEmbed('#nutrition-graph-7-day', vegaSpec)
      .then(() => console.log("Vega graph rendered successfully."))
      .catch(console.error);
});
