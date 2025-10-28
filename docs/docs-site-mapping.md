# Documentation Site Mapping Table

This document tracks which documentation files from the `docs/` folder have been imported and reorganized into the `docs_site/` folder structure.

## Mapping Status

### Getting Started Section

| Source Doc | Target Doc | Status | Notes |
|------------|------------|--------|-------|
| - | getting-started/installation.md | ✅ Exists | Generic installation guide |
| - | getting-started/quick-start.md | ✅ Exists | Generic quick start |
| - | getting-started/configuration.md | ✅ Exists | Generic configuration |

### Features Section

| Source Doc | Target Doc | Status | Notes |
|------------|------------|--------|-------|
| - | features/overview.md | ✅ Exists | Generic features overview |
| analytics_*.* | features/analytics.md | ❌ Need Create | Consolidate analytics docs |
| ARTIST_*.md | features/artist-management.md | ❌ Need Create | Consolidate artist docs |
| acrcloud_*.md | features/acrcloud-analysis.md | ✅ Exists | ACRCloud integration |
| - | features/dynamic-tables-api.md | ✅ Exists | Generic dynamic tables |
| chart_sync_system.md | features/chart-management.md | ❌ Need Update | Chart sync docs |
| - | features/user-management.md | ✅ Exists | Generic user management |
| celery.md | features/background-tasks.md | ❌ Need Update | Celery tasks |

### API Reference Section

| Source Doc | Target Doc | Status | Notes |
|------------|------------|--------|-------|
| - | api/overview.md | ✅ Exists | Generic API overview |
| - | api/external-apis.md | ✅ Exists | Generic external APIs |
| charts-via-api.md | api/internal-apis.md | ❌ Need Update | API endpoints |
| - | api/authentication.md | ✅ Exists | Generic authentication |

### Admin Guide Section

| Source Doc | Target Doc | Status | Notes |
|------------|------------|--------|-------|
| track_admin_alerts_implementation.md | admin/dashboard-overview.md | ❌ Need Update | Dashboard features |
| custom_admin_ordering.md | admin/data-management.md | ❌ Need Update | Admin customization |
| soundcharts_admin_navigation_improvements.md | admin/data-management.md | ❌ Need Update | Admin navigation |
| chart_ranking_admin_dashboard.md | admin/data-management.md | ❌ Need Update | Chart admin |
| track_metadata_integration.md | admin/data-management.md | ❌ Need Update | Metadata management |
| admin_import_templates_consistency.md | admin/data-management.md | ❌ Need Update | Import templates |
| - | admin/task-monitoring.md | ✅ Exists | Generic task monitoring |
| - | admin/user-administration.md | ✅ Exists | Generic user admin |

### Deployment Section

| Source Doc | Target Doc | Status | Notes |
|------------|------------|--------|-------|
| deployment_procedure.md | deployment/production-setup.md | ❌ Need Update | Production deployment |
| ubuntu_deployment_guide.md | deployment/production-setup.md | ❌ Need Update | Ubuntu deployment |
| docker.md | deployment/docker-deployment.md | ✅ Exists | Docker deployment |
| ci-cd.md | deployment/ci-cd-pipeline.md | ✅ Exists | CI/CD pipeline |
| - | deployment/environment-configuration.md | ✅ Exists | Environment config |

### Development Section

| Source Doc | Target Doc | Status | Notes |
|------------|------------|--------|-------|
| ANALYTICS_COMPLETE_SUMMARY.md | development/features-overview.md | ❌ Need Update | Analytics features |
| analytics_technical_architecture.md | development/architecture.md | ❌ Need Update | Technical architecture |
| audience_data_system.md | development/data-models.md | ❌ Need Update | Data models |
| soundcharts_dashboard.md | development/features-overview.md | ❌ Need Update | Soundcharts features |
| hierarchical_genre_model.md | development/data-models.md | ❌ Need Update | Genre model |
| artist_track_relationships.md | development/data-models.md | ❌ Need Update | Relationships |
| admin_import_templates_consistency.md | development/admin-customization.md | ❌ Need Update | Admin customization |
| datatables.md | development/api-frontend-integration.md | ❌ Need Update | Frontend integration |
| chart_sync_system.md | development/features-overview.md | ❌ Need Update | Chart sync |
| artist_audience_integration.md | development/features-overview.md | ❌ Need Update | Artist integration |
| acrcloud_integration.md | development/features-overview.md | ❌ Need Update | ACRCloud integration |
| - | development/contributing.md | ✅ Exists | Contributing guide |
| - | development/testing.md | ✅ Exists | Testing guide |
| csp_troubleshooting.md | development/troubleshooting.md | ❌ Need Update | Troubleshooting |
| static_files_troubleshooting.md | development/troubleshooting.md | ❌ Need Update | Static files troubleshooting |
| gunicorn_troubleshooting.md | development/troubleshooting.md | ❌ Need Update | Gunicorn troubleshooting |
| celery_services_guide.md | development/troubleshooting.md | ❌ Need Update | Celery troubleshooting |

## Document Categories

### Analytics Documentation (features/analytics.md)
- analytics_entry_exit_dates.md
- analytics_excel_export_enhanced.md
- analytics_extension_guide.md
- analytics_phase2_complete.md
- analytics_phase2_track_breakdown_plan.md
- analytics_per_platform_cards.md
- analytics_phase1_complete_enhanced.md
- analytics_phase1_fixes.md
- music_analytics_phase1_complete.md
- analytics_country_filter_enhancement.md
- analytics_critical_fixes_v2.md
- analytics_debugging_guide.md
- analytics_metric_explanations.md
- aggregated_analytics_implementation_plan.md
- aggregated_analytics_refined_approach.md
- aggregated_view_requirements.md
- analytics_bug_fixes_tooltips_export.md
- ANALYTICS_COMPLETE_SUMMARY.md
- analytics_technical_architecture.md

### Artist Documentation (features/artist-management.md)
- ARTIST_DASHBOARD_COMPLETE.md
- ARTIST_IMPLEMENTATION_COMPLETE.md
- ARTIST_INTEGRATION_SUMMARY.md
- artist_dashboard_pages.md
- artist_list_buttons_debugging.md
- artist_list_table_enhancements.md
- artist_track_linking_complete.md
- artist_uuid_validation.md
- artist_audience_form_validation_fix.md
- artist_audience_integration.md
- artist_biography_formatting.md

### Soundcharts Documentation (features/soundcharts-integration.md)
- soundcharts-consolidation-flow-analysis.md
- soundcharts-automated-cascade-implementation.md
- soundcharts_api_fixes.md
- soundcharts_dashboard.md
- chart_cascade_button_implementation.md
- audience_data_system.md
- radio_airplay_implementation.md
- radio_integration_discussion.md
- sync_ranking_entries_fix.md

### ACRCloud Documentation (features/acrcloud-analysis.md)
- acrcloud_derivative_works_fix.md
- acrcloud_pattern_matching_table_fix.md
- acrcloud_bugfixes_20251009.md
- acrcloud_detailed_analysis_enhancement.md
- acrcloud_enhanced_report_implementation.md
- acrcloud_enhanced_report_quickstart.md
- acrcloud_pdf_field_mapping.md
- acrcloud_platform_fix.md
- acrcloud_metadata_integration.md
- acrcloud_credentials_guide.md
- acrcloud_localhost_setup.md
- acrcloud_authentication_fix.md
- acrcloud_setup_guide.md
- acrcloud_webhook_implementation.md
- acrcloud_implementation_summary.md
- acrcloud_integration.md
- acrcloud_setup.md

## Implementation Status

### Completed
- ✅ Basic docs_site structure exists
- ✅ mkdocs.yml is configured
- ✅ Navigation structure is defined
- ✅ Document mapping table created
- ✅ Import analytics documentation (features/analytics.md)
- ✅ Import artist documentation (features/artist-management.md)
- ✅ Import Soundcharts documentation (features/soundcharts-integration.md)
- ✅ Update admin guide docs (admin/data-management.md)
- ✅ Build mkdocs site successfully

## Notes
- Keep detailed technical documentation in the development section
- Consolidate user-facing features in the features section
- Ensure clear separation between user and developer documentation
- PDF files will be linked but not imported into the site
- Some documents contain sensitive or deprecated information - review before importing
