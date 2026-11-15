-- Table Creation
CREATE TABLE ont_communities (
    Category VARCHAR(255),
    Supporting_Ministry VARCHAR(255),
    Community VARCHAR(255),
    Project VARCHAR(255),
    Status VARCHAR(255),
    Target_Completion_Date DATE,
    Description TEXT,
    Result TEXT,
    Area VARCHAR(255),
    Region VARCHAR(255),
    Address VARCHAR(255),
    Postal_Code VARCHAR(255),
    Highway_Transit_Line VARCHAR(255),
    Estimated_Total_Budget DECIMAL(18, 2),
    Municipal_Funding VARCHAR(255),
    Provincial_Funding VARCHAR(255),
    Federal_Funding VARCHAR(255),
    Other_Funding VARCHAR(255),
    Website VARCHAR(255),
    Latitude DECIMAL(10, 8),
    Longitude DECIMAL(11, 8)
);

-- Update character/text columns with 'unknown' if empty
UPDATE ont_communities
SET Category = COALESCE(Category, 'unknown'),
    Supporting_Ministry = COALESCE(Supporting_Ministry, 'unknown'),
    Community = COALESCE(Community, 'unknown'),
    Project = COALESCE(Project, 'unknown'),
    Status = COALESCE(Status, 'unknown'),
    Description = COALESCE(Description, 'unknown'),
    Result = COALESCE(Result, 'unknown'),
    Area = COALESCE(Area, 'unknown'),
    Region = COALESCE(Region, 'unknown'),
    Address = COALESCE(Address, 'unknown'),
    Postal_Code = COALESCE(Postal_Code, 'unknown'),
    Highway_Transit_Line = COALESCE(Highway_Transit_Line, 'unknown'),
    Website = COALESCE(Website, 'unknown'),
    Municipal_Funding = COALESCE(Municipal_Funding, 'unknown'),
    Provincial_Funding = COALESCE(Provincial_Funding, 'unknown'),
    Federal_Funding = COALESCE(Federal_Funding, 'unknown'),
    Other_Funding = COALESCE(Other_Funding, 'unknown');

-- Update number columns with 0 if empty
UPDATE ont_communities
SET Estimated_Total_Budget = COALESCE(Estimated_Total_Budget, 0),
    Latitude = COALESCE(Latitude, 0),
    Longitude = COALESCE(Longitude, 0);

-- Import the csv file using the file icon on posgres
-- DATA CLEANING PROCESS

-- Update character/text columns with 'unknown' if empty
UPDATE ont_communities
SET Category = COALESCE(Category, 'unknown'),
    Supporting_Ministry = COALESCE(Supporting_Ministry, 'unknown'),
    Community = COALESCE(Community, 'unknown'),
    Project = COALESCE(Project, 'unknown'),
    Status = COALESCE(Status, 'unknown'),
    Description = COALESCE(Description, 'unknown'),
    Result = COALESCE(Result, 'unknown'),
    Area = COALESCE(Area, 'unknown'),
    Region = COALESCE(Region, 'unknown'),
    Address = COALESCE(Address, 'unknown'),
    Postal_Code = COALESCE(Postal_Code, 'unknown'),
    Highway_Transit_Line = COALESCE(Highway_Transit_Line, 'unknown'),
    Website = COALESCE(Website, 'unknown'),
    Municipal_Funding = COALESCE(Municipal_Funding, 'unknown'),
    Provincial_Funding = COALESCE(Provincial_Funding, 'unknown'),
    Federal_Funding = COALESCE(Federal_Funding, 'unknown'),
    Other_Funding = COALESCE(Other_Funding, 'unknown');

-- Update number columns with 0 if empty
UPDATE ont_communities
SET Estimated_Total_Budget = COALESCE(Estimated_Total_Budget, 0),
    Latitude = COALESCE(Latitude, 0),
    Longitude = COALESCE(Longitude, 0);

-- Check for duplicate rows
SELECT *
FROM ont_communities
GROUP BY Category, Supporting_Ministry, Community, Project, Status, Target_Completion_Date, Description, Result, Area, Region, Address, Postal_Code, Highway_Transit_Line, Estimated_Total_Budget, Municipal_Funding, Provincial_Funding, Federal_Funding, Other_Funding, Website, Latitude, Longitude
HAVING COUNT(*) > 1;

--Deleting duplicate rows

CREATE TEMPORARY TABLE temp_unique_rows AS
SELECT DISTINCT *
FROM ont_communities;

TRUNCATE TABLE ont_communities;

INSERT INTO ont_communities
SELECT *
FROM temp_unique_rows;

DROP TABLE temp_unique_rows;


-- TABLES CREATION

CREATE TABLE community (
    id SERIAL PRIMARY KEY,
    comname VARCHAR(255) UNIQUE
);

INSERT INTO community (comname)
SELECT DISTINCT Community FROM ont_communities;

CREATE TABLE status (
    id SERIAL PRIMARY KEY,
    statname VARCHAR(255) UNIQUE
);

INSERT INTO status (statname)
SELECT DISTINCT Status FROM ont_communities;

CREATE TABLE ministry (
    id SERIAL PRIMARY KEY,
    minname VARCHAR(255) UNIQUE
);

INSERT INTO ministry (minname)
SELECT DISTINCT Supporting_Ministry FROM ont_communities;

CREATE TABLE project (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255),
    status_id INT REFERENCES status(id),
    ministry_id INT REFERENCES ministry(id),
    community_id INT REFERENCES community(id),
    Target_Completion_Date DATE,
    Description TEXT,
    Result TEXT,
    Area VARCHAR(255),
    Region VARCHAR(255),
    Address VARCHAR(255),
    Postal_Code VARCHAR(255),
    Highway_Transit_Line VARCHAR(255),
    Estimated_Total_Budget DECIMAL(18, 2),
    Municipal_Funding VARCHAR(255),
    Provincial_Funding VARCHAR(255),
    Federal_Funding VARCHAR(255),
    Other_Funding VARCHAR(255),
    Website VARCHAR(255),
    Latitude DECIMAL(10, 8),
    Longitude DECIMAL(11, 8)
);

INSERT INTO project (project_name, status_id, ministry_id, community_id, Target_Completion_Date, Description, Result, Area, Region, Address, Postal_Code, Highway_Transit_Line, Estimated_Total_Budget, Municipal_Funding, Provincial_Funding, Federal_Funding, Other_Funding, Website, Latitude, Longitude)
SELECT 
    Project,
    (SELECT id FROM status WHERE statname = ont_communities.Status) as Status_id,
    (SELECT id FROM ministry WHERE minname = ont_communities.Supporting_Ministry) as Ministry_id,
    (SELECT id FROM community WHERE comname = ont_communities.Community) as Community_id,
    Target_Completion_Date,
    Description,
    Result,
    Area,
    Region,
    Address,
    Postal_Code,
    Highway_Transit_Line,
    Estimated_Total_Budget,
    Municipal_Funding,
    Provincial_Funding,
    Federal_Funding,
    Other_Funding,
    Website,
    Latitude,
    Longitude
FROM
    ont_communities;




-- OTHER SQL QUERIES:

-- Query 1: List of all projects along with their associated community names
SELECT p.project_name, c.comname
FROM project p
INNER JOIN community c ON p.community_id = c.id;

-- Query 2: Number of projects in each ministry
SELECT m.minname, COUNT(*) AS project_count
FROM project p
INNER JOIN ministry m ON p.ministry_id = m.id
GROUP BY m.minname;

-- Query 3: Total budget allocated for projects in each region
SELECT p.region, SUM(p.estimated_total_budget) AS total_budget
FROM project p
GROUP BY p.region;

-- Query 4: Projects with their status
SELECT p.project_name, s.statname
FROM project p
INNER JOIN status s ON p.status_id = s.id;

-- Query 5: Average budget of projects in each community
SELECT c.comname, ROUND(AVG(p.estimated_total_budget), 2) AS avg_budget
FROM project p
INNER JOIN community c ON p.community_id = c.id
GROUP BY c.comname;

-- Query 6: Projects with a completion date past the target completion date
SELECT project_name, target_completion_date
FROM project
WHERE target_completion_date < CURRENT_DATE;

-- Query 7: Total funding received for projects in each region
SELECT p.region, SUM(p.estimated_total_budget) AS total_funding
FROM project p
GROUP BY p.region;

-- Query 8: Total budget allocated to projects for each ministry in a specific region
SELECT m.minname, p.region, SUM(p.estimated_total_budget) AS total_budget
FROM project p
INNER JOIN ministry m ON p.ministry_id = m.id
GROUP BY m.minname, p.region;

-- Query 9: Projects with the highest estimated total budget
SELECT project_name, estimated_total_budget
FROM project
ORDER BY estimated_total_budget DESC
LIMIT 5;

-- Query 10: Number of projects in each status for a specific ministry
SELECT m.minname, s.statname, COUNT(*) AS project_count
FROM project p
INNER JOIN ministry m ON p.ministry_id = m.id
INNER JOIN status s ON p.status_id = s.id
GROUP BY m.minname, s.statname
ORDER BY m.minname;
