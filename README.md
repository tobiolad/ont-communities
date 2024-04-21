# Ontario Community Infrastructure Projects Analysis

## Introduction

This project focuses on analyzing infrastructure projects in Ontario, Canada, using data from the Welcome Ontario dataset. The dataset contains valuable information about key infrastructure projects across various communities in Ontario, including project details, budgets, statuses, and completion dates. The objective of this project is to extract insights from the data to inform decision-making and project management within government infrastructure and community development initiatives.

## Dataset

The dataset used for this analysis is sourced from the Welcome Ontario Data Catalogue, accessible at the following link: [Welcome Ontario Data Catalogue](https://data.ontario.ca/dataset/ontario-builds-key-infrastructure-projects/resource/36f92c5b-0c8b-4a4b-b4c5-d15a43894297)

## Data Processing

### Table Creation

We started by creating a PostgreSQL database table called `ont_communities` to store the dataset. The table includes columns for various project attributes such as category, supporting ministry, community, project name, status, target completion date, description, result, area, region, address, postal code, funding details, and geographical coordinates.

### Data Cleaning and Transformation

We performed data cleaning and transformation tasks to ensure the consistency and reliability of the dataset. This included updating empty text fields with 'unknown' and empty numerical fields with 0 to avoid processing errors. We also removed duplicate entries from the dataset to maintain data integrity.

### SQL Scripts

All SQL scripts used for data processing, including table creation, data cleaning, and transformation, are provided in the `sql_scripts` directory. These scripts can be executed in a PostgreSQL environment to replicate the data processing steps.

## Analysis and Insights

We conducted an in-depth analysis of the dataset to extract meaningful insights that could aid decision-making and project management. This included formulating SQL queries to answer key questions such as:

- List of all projects along with their associated community names
- Number of projects in each ministry
- Total budget allocated for projects in each region
- Projects with their status
- Average budget of projects in each community
- Projects with completion dates past the target completion date
- Total funding received for projects in each region
- Total budget allocated to projects for each ministry in a specific region
- Projects with the highest estimated total budget
- Number of projects in each status for a specific ministry

The SQL queries and their results are documented in the `analysis_insights.sql` file.

## Visualizations

We created visualizations such as charts, graphs, and maps to illustrate the insights derived from the data analysis. These visualizations enhance the comprehension of key findings and trends in the dataset. Sample visualizations are included in the `visualizations` directory.

## Summary and Findings

The project summary and key findings are documented in the `summary_findings.docx` file. This includes a narrative overview of the insights obtained from the data analysis and their implications for infrastructure and community development initiatives in Ontario.

## Usage

To replicate the analysis:

1. Clone this repository to your local machine.
2. Set up a PostgreSQL database and execute the SQL scripts in the `sql_scripts` directory to create the database table and perform data processing.
3. Review the analysis insights documented in the `analysis_insights.sql` file.
4. Refer to the summary and findings documented in the `summary_findings.docx` file for a comprehensive overview of the project.

## Contributors

- Tobi Oladimeji
- Sushma Gouri Deivanayagam
- Sachin Suresh
- Dwij Shyamsunder
- Surya Amit Malwade

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

We would like to thank the Ontario government for providing access to the Welcome Ontario dataset, which served as the foundation for this analysis.
