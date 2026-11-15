-- Convenience view joining every dimension onto fact_project. Both the API
-- and the example SQL analysis queries read from this view, so the numbers
-- shown in the dashboard and the numbers in docs/SQL_EXAMPLES.md are
-- guaranteed to come from the same definition.

CREATE OR REPLACE VIEW v_project AS
SELECT
    fp.project_id,
    fp.project_name,
    fp.description,
    fp.result,
    fp.category,
    fp.area,
    dc.community_name,
    dr.region_name,
    dm.ministry_name,
    ds.status_name,
    fp.address,
    fp.postal_code,
    fp.latitude,
    fp.longitude,
    fp.coordinate_status,
    fp.multi_point_raw,
    fp.highway_transit_line,
    fp.target_completion_date_raw,
    fp.target_completion_precision,
    fp.target_completion_upper_bound,
    (fp.target_completion_upper_bound IS NOT NULL
        AND fp.target_completion_upper_bound < CURRENT_DATE) AS target_window_passed,
    fp.estimated_total_budget,
    fp.budget_undisclosed,
    fp.municipal_funded,
    fp.provincial_funded,
    fp.federal_funded,
    fp.other_funded,
    fp.website,
    fp.batch_id,
    fp.created_at,
    fp.updated_at
FROM fact_project fp
LEFT JOIN dim_community dc ON fp.community_id = dc.community_id
LEFT JOIN dim_region dr ON fp.region_id = dr.region_id
LEFT JOIN dim_ministry dm ON fp.ministry_id = dm.ministry_id
JOIN dim_status ds ON fp.status_id = ds.status_id;
