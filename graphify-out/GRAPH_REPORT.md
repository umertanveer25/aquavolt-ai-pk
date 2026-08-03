# Graph Report - .  (2026-08-03)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2504 nodes · 4997 edges · 218 communities (168 shown, 50 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 124 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `63063284`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- LogRepository
- .execute
- idea.repository.ts
- request.repository.ts
- bug.repository.ts
- agency-service
- AquaVoltMainWindow
- tauri.ts
- message.repository.ts
- DatabaseAdapter
- aquavolt_gsheet_logger.py
- _log-helper
- requests
- main.rs
- TestConfigService
- observation.service.ts
- datetime
- test-run.repository.ts
- secret.service.ts
- aquavolt_logger.py
- SecretRepository
- secret
- secret.repository.ts
- secret-service/types.ts
- starter-test
- auth.middleware.ts
- log
- SQLiteQueueAdapter
- starter-compare
- gibs_viirs_integration.py
- SQLiteAdapter
- TestService
- agency-service/src/index.ts
- observation.repository.ts
- project-update
- api/main.py
- QueueAdapter
- Secret
- myclaude
- test_helper.bash
- TestPluginRegistry
- TestDiscoveryService
- test-runner.ts
- test-service/types.ts
- starter-release
- TestPIMLConstraints
- version-next
- train_piml_weights_subfield.py
- claude/claude-desktop/agency-server/index.ts
- integrations/claude-desktop/agency-server/index.ts
- workitems/page.tsx
- logger.ts
- dependencies-install
- designsystem-validate
- docbench
- figma-extract
- observe
- release
- request
- requests-backfill
- LSTMForecaster
- TestDataPipeline
- TestLSTMForecaster
- TestFAO56Physics
- TOOL.sh
- SecretService
- message-send
- sync
- agent-create
- collaboration-respond
- commit-precheck
- designsystem-add
- tool-new
- test_aquavolt.py
- TestStatistics
- secrets/page.tsx
- add-principal
- artifact-index-update
- bench
- browser
- collaborate
- figma-diff
- linux-setup
- mac-setup
- news-post
- news-read
- principal-create
- secret-migrate
- session-archive
- setup-agency
- starter-update
- gee_et_api.py
- createSecretRoutes
- adhoc-log
- agency-feedback
- agentname
- artifact-capture
- artifact-list
- commit
- commit-prefix
- config
- context-review
- context-save
- dependencies-check
- epic-create
- icloud-setup
- instruction-capture
- instruction-complete
- instruction-index-update
- instruction-list
- instruction-show
- iterm-setup
- now
- principal
- project-create
- proposal-capture
- restore
- session-backup
- sprint-create
- starter-cleanup
- starter-verify
- tag
- test-run
- tool-version-add
- version-bump
- welcomeback
- whoami
- workstream
- workstream-create
- gcp_function/main.py
- main
- .grantAccess
- bench-build
- message-read
- agency-bench
- ecostress_api.py
- git-ci/install.sh
- nextjs-react/install.sh
- supabase/install.sh
- vercel/install.sh
- next.config.ts
- bugbench/page.tsx
- review-spawn
- secrets-scan
- .agency-starter/install.sh
- findings-consolidate
- findings-save
- ensemble_fusion.py
- generate_plots.py
- cimis_api.py
- noaa_uscrn.py
- usda_scan.py
- update_satellite_image.py
- session-end.sh
- app/layout.tsx
- ui/src/index.ts
- SecretStats
- requests-backfill.test.ts
- load_data
- dynamic_registry.py
- analyze_spatial_decay.py
- task2_directional.py
- esa_sentinel2.py
- nasa_gpm.py
- nasa_modis_nbar.py
- nasa_power.py
- nasa_smap.py
- openlandmap.py
- ucsb_chirps.py
- force_dashboard.py
- test_reprojection.py
- agency
- agency-bench/next-env.d.ts
- messages-check.sh
- session-start.sh
- statusline.sh
- tauri-app/next-env.d.ts
- setup.sh
- tailwind.config.ts
- agency-update
- gh-api
- gh-pr
- gh-release
- install-hooks
- launch-project
- log-tool-use
- log-tool-use-debug
- opportunities
- task1_diurnal.py
- task3_vpd_interaction.py
- task4_irrigation_penalty.py
- create_teaser_data.py
- fix_3_plugins.py
- fix_final_2.py
- inject_open_source_apis.py
- verify_aspect.py

## God Nodes (most connected - your core abstractions)
1. `DatabaseAdapter` - 79 edges
2. `createServiceLogger()` - 44 edges
3. `SecretRepository` - 43 edges
4. `SecretService` - 35 edges
5. `createSecretRoutes()` - 33 edges
6. `TestService` - 33 edges
7. `QueueAdapter` - 30 edges
8. `createSQLiteAdapter()` - 29 edges
9. `LogRepository` - 27 edges
10. `LogService` - 26 edges

## Surprising Connections (you probably didn't know these)
- `TestDataIntegrity` --uses--> `LSTMForecaster`  [INFERRED]
  tests/test_aquavolt.py → lstm_forecaster.py
- `TestDataPipeline` --uses--> `LSTMForecaster`  [INFERRED]
  tests/test_aquavolt.py → lstm_forecaster.py
- `TestFAO56Physics` --uses--> `LSTMForecaster`  [INFERRED]
  tests/test_aquavolt.py → lstm_forecaster.py
- `TestLSTMForecaster` --uses--> `LSTMForecaster`  [INFERRED]
  tests/test_aquavolt.py → lstm_forecaster.py
- `TestPIMLConstraints` --uses--> `LSTMForecaster`  [INFERRED]
  tests/test_aquavolt.py → lstm_forecaster.py

## Import Cycles
- 3-file cycle: `.agency-starter/source/services/agency-service/src/core/lib/logger.ts -> .agency-starter/source/services/agency-service/src/embedded/log-service/service/log.service.ts -> .agency-starter/source/services/agency-service/src/embedded/log-service/repository/log.repository.ts -> .agency-starter/source/services/agency-service/src/core/lib/logger.ts`
- 5-file cycle: `.agency-starter/source/services/agency-service/src/core/adapters/database/index.ts -> .agency-starter/source/services/agency-service/src/core/adapters/database/sqlite.adapter.ts -> .agency-starter/source/services/agency-service/src/core/lib/logger.ts -> .agency-starter/source/services/agency-service/src/embedded/log-service/service/log.service.ts -> .agency-starter/source/services/agency-service/src/embedded/log-service/repository/log.repository.ts -> .agency-starter/source/services/agency-service/src/core/adapters/database/index.ts`

## Communities (218 total, 50 thin omitted)

### Community 0 - "LogRepository"
Cohesion: 0.06
Nodes (36): logger, LogServiceInstance, LogServiceOptions, LogEntryRow, logger, LogRepository, rowToLogEntry(), rowToToolRun() (+28 more)

### Community 1 - ".execute"
Cohesion: 0.07
Nodes (30): createProductService(), ContributorRow, CountRow, logger, PriorityCountRow, ProductRepository, ProductRow, rowToContributor() (+22 more)

### Community 2 - "idea.repository.ts"
Cohesion: 0.07
Nodes (35): IdeaServiceInstance, IdeaServiceOptions, logger, escapeLikePattern(), getSortColumn(), IdeaRepository, IdeaRow, logger (+27 more)

### Community 3 - "request.repository.ts"
Cohesion: 0.07
Nodes (35): RequestServiceInstance, escapeLikePattern(), getSortColumn(), logger, normalizeSortDirection(), RequestRepository, RequestRow, rowToRequest() (+27 more)

### Community 4 - "bug.repository.ts"
Cohesion: 0.08
Nodes (32): BugServiceInstance, logger, BugRepository, BugRow, escapeLikePattern(), getSortColumn(), logger, normalizeSortDirection() (+24 more)

### Community 5 - "agency-service"
Cohesion: 0.11
Nodes (54): agency-service script, api_request(), cmd_api_info(), cmd_bug_assign(), cmd_bug_create(), cmd_bug_get(), cmd_bug_list(), cmd_bug_stats() (+46 more)

### Community 6 - "AquaVoltMainWindow"
Cohesion: 0.06
Nodes (23): AquaVoltMainWindow, build_nasa_power_url(), build_open_meteo_url(), compute_penman_et0(), CropSectorGrid, NasaPowerWorker, NDVIOpenAccessWorker, OpenMeteoWorker (+15 more)

### Community 7 - "tauri.ts"
Cohesion: 0.06
Nodes (33): Agent, Collaboration, DocBenchContent(), TreeNode, SearchMatch, SearchResult, Message, MessageRecipient (+25 more)

### Community 8 - "message.repository.ts"
Cohesion: 0.09
Nodes (25): logger, MessagesServiceInstance, logger, MessageRepository, MessageRow, RecipientRow, rowToMessage(), rowToRecipient() (+17 more)

### Community 9 - "DatabaseAdapter"
Cohesion: 0.10
Nodes (11): createDatabaseAdapter(), TODO: Implement PostgreSQL adapter when needed, createSQLiteAdapter(), logger, DatabaseAdapter, DatabaseAdapterFactory, DatabaseConfig, logger (+3 more)

### Community 10 - "aquavolt_gsheet_logger.py"
Cohesion: 0.07
Nodes (36): build_url(), _calc_stats(), compute_lai_fcover(), fetch_chirps_precipitation(), fetch_copernicus_dem_slope(), fetch_era5_bias_correction(), fetch_field_indices(), fetch_modis_lst() (+28 more)

### Community 11 - "_log-helper"
Cohesion: 0.08
Nodes (22): bug-report script, code-review script, gh script, log_end(), hello script, hi script, _log-helper script, _log_debug() (+14 more)

### Community 12 - "requests"
Cohesion: 0.06
Nodes (22): requests script, check_service(), format_list_output(), log_error(), log_info(), log_warn(), main(), fetch() (+14 more)

### Community 13 - "main.rs"
Cohesion: 0.15
Nodes (33): check_context_saved(), get_git_status(), main(), parse_transcript_for_todos(), Check if a file should be excluded from uncommitted changes check., Check for uncommitted changes., Check if context was saved recently (within this session)., Parse transcript to find TODO state. (+25 more)

### Community 14 - "TestConfigService"
Cohesion: 0.09
Nodes (12): ALLOWED_RUNNER_COMMANDS, getDefaultConfig(), logger, TestConfigService, ConfigValidationResult, TestConfig, testConfigSchema, TestRunner (+4 more)

### Community 15 - "observation.service.ts"
Cohesion: 0.15
Nodes (17): createObservationRoutes(), logger, updateStatusSchema, logger, ObservationService, CreateObservationInput, CreateObservationSchema, EntityType (+9 more)

### Community 16 - "datetime"
Cohesion: 0.06
Nodes (19): datetime, fetch(), Fetches real hourly ground-level weather for Davis, CA via Open-Meteo (mirrors…, fetch(), Fetches real ERA5-Land reanalysis data via Open-Meteo archive API., fetch(), Searches NASA CMR STAC for latest Sentinel-3 data over Russell Ranch., fetch() (+11 more)

### Community 17 - "test-run.repository.ts"
Cohesion: 0.11
Nodes (12): logger, rowToTestResult(), rowToTestRun(), TestResultRow, TestRunRepository, TestRunRow, QueryTestRunsRequest, TestResult (+4 more)

### Community 18 - "secret.service.ts"
Cohesion: 0.13
Nodes (11): rowToTag(), Accessor, logger, AddTagRequest, AuditAction, RemoveTagRequest, RevokeAccessRequest, RotateSecretRequest (+3 more)

### Community 19 - "aquavolt_logger.py"
Cohesion: 0.11
Nodes (25): archive_previous_month_to_git(), build_url(), compute_lai_fcover(), fao56_kc_prior(), fetch_and_store(), fetch_field_indices(), fetch_modis_lst(), fetch_open_meteo_forecast() (+17 more)

### Community 20 - "SecretRepository"
Cohesion: 0.12
Nodes (5): decrypt(), hashSessionToken(), SecretRepository, VaultStatus, VaultStatusResponse

### Community 21 - "secret"
Cohesion: 0.15
Nodes (20): secret script, api_request(), cmd_audit(), cmd_create(), cmd_delete(), cmd_get(), cmd_grant(), cmd_list() (+12 more)

### Community 22 - "secret.repository.ts"
Cohesion: 0.10
Nodes (19): ARGON2_CONFIG, AuditRow, ConfigRow, CountRow, deriveKey(), deriveKeyFromPassphrase(), generateRecoveryCode(), generateSalt() (+11 more)

### Community 23 - "secret-service/types.ts"
Cohesion: 0.12
Nodes (23): logger, addTagSchema, auditActionSchema, createSecretSchema, findByTagQuerySchema, grantAccessSchema, InitVaultRequest, initVaultSchema (+15 more)

### Community 24 - "starter-test"
Cohesion: 0.29
Nodes (24): starter-test script, cleanup(), log_detail(), log_error(), log_fail(), log_info(), log_pass(), log_step() (+16 more)

### Community 25 - "auth.middleware.ts"
Cohesion: 0.16
Nodes (17): Config, configSchema, findProjectRoot(), getConfig(), loadConfig(), resetConfig(), authMiddleware(), AuthUser (+9 more)

### Community 26 - "log"
Cohesion: 0.17
Nodes (19): log script, api_request(), cmd_commands(), cmd_failures(), cmd_query(), cmd_run_end(), cmd_run_errors(), cmd_run_get() (+11 more)

### Community 27 - "SQLiteQueueAdapter"
Cohesion: 0.16
Nodes (8): logger, QueueRow, SQLiteQueueAdapter, QueueAdapterFactory, QueueConfig, QueueHandler, QueueJob, QueueSubscription

### Community 28 - "starter-compare"
Cohesion: 0.24
Nodes (20): starter-compare script, check_required_files(), compare_contents(), compare_file_lists(), create_install(), fix_source(), init_logging(), log() (+12 more)

### Community 29 - "gibs_viirs_integration.py"
Cohesion: 0.12
Nodes (18): fetch_thermal_cascading(), detect_observation_gap(), fetch_gibs_tile(), fetch_viirs_lst(), fetch_viirs_ndvi(), fill_gap_with_gibs(), _get_t2m(), integrate_into_pipeline() (+10 more)

### Community 31 - "TestService"
Cohesion: 0.16
Nodes (8): DiscoveredSuite, TestServiceInstance, createTestRoutes(), runTestsWithConfig(), TestService, CreateTestRunRequest, TestRunWithResults, TestSuite

### Community 32 - "agency-service/src/index.ts"
Cohesion: 0.19
Nodes (17): closeDatabase(), getDatabase(), closeQueue(), createQueueAdapter(), getQueue(), TODO: Implement Redis/BullMQ adapter when needed, createSQLiteQueueAdapter(), loggingMiddleware() (+9 more)

### Community 33 - "observation.repository.ts"
Cohesion: 0.15
Nodes (12): createObservationService(), ObservationServiceConfig, ObservationServiceInstance, escapeLikePattern(), getSortColumn(), logger, normalizeSortDirection(), ObservationRepository (+4 more)

### Community 34 - "project-update"
Cohesion: 0.15
Nodes (10): project-update script, check_mode(), cleanup(), init_mode(), is_protected(), log_error(), main(), merge_claude_md() (+2 more)

### Community 35 - "api/main.py"
Cohesion: 0.16
Nodes (17): get_data(), get_field_recommendation(), get_historical_telemetry(), get_latest_telemetry(), get_satellite_status(), get_water_deficit_forecast(), AquaVolt-AI REST API ==================== FastAPI server providing programmatic…, **FREE TIER** — Returns the last 24 hours of telemetry data. No API key… (+9 more)

### Community 36 - "QueueAdapter"
Cohesion: 0.12
Nodes (6): QueueAdapter, BugServiceOptions, MessagesServiceOptions, logger, RequestServiceOptions, REPO_ROOT

### Community 37 - "Secret"
Cohesion: 0.20
Nodes (8): encrypt(), rowToSecret(), rowToSecretWithValue(), CreateSecretRequest, ListSecretsQuery, Secret, SecretWithValue, UpdateSecretRequest

### Community 38 - "myclaude"
Cohesion: 0.27
Nodes (15): myclaude script, AGENT_NAME, AGENTNAME, check_python_deps(), check_services(), log_debug(), log_error(), log_info() (+7 more)

### Community 39 - "test_helper.bash"
Cohesion: 0.12
Nodes (5): test_helper.bash script, LOG_SERVICE_URL, PATH, REPO_ROOT, TOOLS_DIR

### Community 40 - "TestPluginRegistry"
Cohesion: 0.13
Nodes (8): fixture, Validate the auto-discovery plugin registry., At least 15 sensor plugins must be loaded (robust minimum)., Every plugin must have a SENSOR_INFO dict with required keys., Every plugin must expose a callable fetch() function., No two plugins should report the same name (prevents confusion)., Every plugin's SENSOR_INFO name must be a non-empty string., TestPluginRegistry

### Community 42 - "test-runner.ts"
Cohesion: 0.20
Nodes (11): TestTarget, ConfigurableRunnerOptions, extractErrorMessage(), logger, parseBunOutput(), runTests(), TestRunnerOptions, validateSuiteName() (+3 more)

### Community 43 - "test-service/types.ts"
Cohesion: 0.16
Nodes (10): cleanupSchema, logger, createTestRunSchema, FlakyTest, queryTestRunsSchema, TestResultStatus, TestRunListResponse, TestRunStatus (+2 more)

### Community 44 - "starter-release"
Cohesion: 0.27
Nodes (11): starter-release script, build_agencybench(), clean_cruft(), log_error(), log_info(), log_step(), log_warn(), sync_files() (+3 more)

### Community 45 - "TestPIMLConstraints"
Cohesion: 0.20
Nodes (8): Validate the Physics-Informed ML sigmoid crop coefficient prior., FAO-56 Sigmoid Prior: Kc = 0.15 + 0.95 / (1 + exp(-12*(NDVI - 0.4))), NDVI ~ 0 (bare soil) → Kc should be near 0.15 (minimum)., NDVI ~ 0.9 (dense vegetation) → Kc should approach 1.1., NDVI = 0.4 should be the inflection point → Kc ≈ 0.625., Kc must increase monotonically with NDVI., Kc must always remain within [0.15, 1.20] after clipping., TestPIMLConstraints

### Community 46 - "version-next"
Cohesion: 0.27
Nodes (10): version-next script, increment_build(), increment_major(), increment_minor(), increment_patch(), log_error(), log_info(), main() (+2 more)

### Community 47 - "train_piml_weights_subfield.py"
Cohesion: 0.27
Nodes (8): extract_ecostress_5x5(), fao56_kc_prior(), fetch_field_indices_5x5(), get_sentinel_items_for_date(), main(), PIMLNet, Fetches a 5x5 sub-field grid of NDVI, NDWI, SAVI for a specific bbox. Uses…, Extracts a 5x5 grid from the ECOSTRESS GeoTIFF for the bbox.

### Community 48 - "claude/claude-desktop/agency-server/index.ts"
Cohesion: 0.18
Nodes (7): ALLOWED_TOOLS, __dirname, __filename, getAgentStatus(), isValidName(), PROJECT_ROOT, server

### Community 49 - "integrations/claude-desktop/agency-server/index.ts"
Cohesion: 0.18
Nodes (7): ALLOWED_TOOLS, __dirname, __filename, getAgentStatus(), isValidName(), PROJECT_ROOT, server

### Community 50 - "workitems/page.tsx"
Cohesion: 0.23
Nodes (10): BaseItem, Bug, Idea, Observation, PRIORITY_COLORS, Request, STATUS_COLORS, TAB_CONFIG (+2 more)

### Community 51 - "logger.ts"
Cohesion: 0.30
Nodes (8): createLogger(), createLogServiceStream(), createServiceLogger(), disableLogServiceDualWrite(), enableLogServiceDualWrite(), getLogger(), isLogServiceDualWriteEnabled(), logger

### Community 52 - "dependencies-install"
Cohesion: 0.35
Nodes (8): dependencies-install script, install_dep(), install_yq(), log_error(), log_step(), main(), usage(), verbose_echo()

### Community 53 - "designsystem-validate"
Cohesion: 0.20
Nodes (3): designsystem-validate script, main(), show_help()

### Community 54 - "docbench"
Cohesion: 0.23
Nodes (5): docbench script, add_to_recent(), launch_docbench(), main(), write_pending()

### Community 55 - "figma-extract"
Cohesion: 0.33
Nodes (9): figma-extract script, extract_embedded_colors(), extract_embedded_fonts(), log_error(), log_info(), log_step(), log_warn(), main() (+1 more)

### Community 56 - "observe"
Cohesion: 0.20
Nodes (3): observe script, main(), show_usage()

### Community 57 - "release"
Cohesion: 0.26
Nodes (6): release script, log_error(), log_info(), log_warn(), main(), verbose_echo()

### Community 58 - "request"
Cohesion: 0.27
Nodes (6): request script, log_error(), log_warn(), main(), show_usage(), verbose_echo()

### Community 59 - "requests-backfill"
Cohesion: 0.29
Nodes (8): requests-backfill script, extract_and_import(), log_error(), log_info(), log_step(), log_warn(), main(), update_sequence()

### Community 60 - "LSTMForecaster"
Cohesion: 0.21
Nodes (5): LSTMForecaster, Predicts the next 24 hours of crop water deficit. current_readings: list of 12…, Loads historical weather and crop telemetry from database or returns simulated…, Generates 7 days (168 hours) of hourly agricultural and weather logs for…, Trains the LSTM network if TensorFlow is available, otherwise prepares…

### Community 61 - "TestDataPipeline"
Cohesion: 0.17
Nodes (7): Validate data structures and pipeline logic., Water deficit = ETc - effective_precip. Must be non-negative (clipped)., If precipitation exceeds ETc, deficit must be zero., Soil moisture stress coefficient Ks must be in [0, 1]., Each field must generate exactly 64 sectors (8x8 grid)., 4 fields × 64 sectors = 256 rows per hourly cycle., TestDataPipeline

### Community 62 - "TestLSTMForecaster"
Cohesion: 0.17
Nodes (7): Validate the LSTM water deficit forecasting module., Synthetic history must have 168 rows (7 days × 24 hours) and 8 columns., Synthetic history must not contain any NaN values., predict_24h() must always return exactly 24 values., Water deficit forecast values must all be >= 0 (no negative water need)., predict_24h() must handle a list of 12 hourly dicts as input., TestLSTMForecaster

### Community 63 - "TestFAO56Physics"
Cohesion: 0.17
Nodes (7): Validate the thermodynamic equations used in the ET₀ calculation., Tetens formula: es(T) = 0.6108 * exp(17.27*T / (T+237.3)), Delta = 4098 * es / (T + 237.3)^2, Gamma = 0.0665 * P (kPa), P ~ 101.3 at sea level, Net radiation should be positive during a sunny day., Reference ET₀ for a California summer day should be 4-10 mm/day., TestFAO56Physics

### Community 64 - "TOOL.sh"
Cohesion: 0.33
Nodes (9): end_run(), log(), log_error(), log_info(), log_warn(), main(), output_success(), TOOL.sh script (+1 more)

### Community 65 - "SecretService"
Cohesion: 0.24
Nodes (5): logger, SecretServiceConfig, SecretServiceInstance, SecretService, RecoveryCodesResponse

### Community 66 - "message-send"
Cohesion: 0.24
Nodes (4): message-send script, add_recipient(), init_db(), show_usage()

### Community 67 - "sync"
Cohesion: 0.38
Nodes (10): sync script, end_run(), log(), log_error(), log_info(), log_warn(), main(), output_failure() (+2 more)

### Community 68 - "agent-create"
Cohesion: 0.33
Nodes (6): agent-create script, log_error(), log_info(), log_step(), main(), verbose_echo()

### Community 69 - "collaboration-respond"
Cohesion: 0.38
Nodes (9): collaboration-respond script, handle_merge_conflict(), log_error(), log_info(), log_step(), log_warn(), main(), sed_i() (+1 more)

### Community 70 - "commit-precheck"
Cohesion: 0.42
Nodes (9): commit-precheck script, end_run(), log(), log_error(), log_info(), log_warn(), main(), output_failure() (+1 more)

### Community 71 - "designsystem-add"
Cohesion: 0.29
Nodes (5): designsystem-add script, log_step(), main(), show_help(), verbose_echo()

### Community 72 - "tool-new"
Cohesion: 0.31
Nodes (6): tool-new script, log_error(), log_info(), log_step(), main(), verbose_echo()

### Community 73 - "test_aquavolt.py"
Cohesion: 0.20
Nodes (6): AquaVolt-AI Unit Tests ====================== Validates the core physics…, Ensure no synthetic generation is used for validation., Random data generation is strictly banned in the telemetry logger., Synthetic plot generation (np.random in generate_plots.py) is strictly banned., AmeriFlux references are banned — no tower exists near the site., TestDataIntegrity

### Community 74 - "TestStatistics"
Cohesion: 0.20
Nodes (6): Validate the statistical functions used for ground-truth benchmarking., Perfect linear data should yield R² = 1.0., RMSE of identical arrays must be zero., If predictions are higher than truth, mean bias must be positive., RMSE must be non-negative for any data., TestStatistics

### Community 75 - "secrets/page.tsx"
Cohesion: 0.22
Nodes (7): AuditLog, Secret, SECRET_TYPE_COLORS, SECRET_TYPE_LABELS, SecretType, VaultStatus, VaultStatusResponse

### Community 76 - "add-principal"
Cohesion: 0.44
Nodes (8): add-principal script, log_error(), log_info(), log_step(), log_warn(), main(), usage(), verbose_echo()

### Community 77 - "artifact-index-update"
Cohesion: 0.33
Nodes (4): artifact-index-update script, main(), update_principal_index(), verbose_echo()

### Community 78 - "bench"
Cohesion: 0.39
Nodes (7): bench script, install_app(), log_error(), log_info(), log_step(), main(), verbose_echo()

### Community 79 - "browser"
Cohesion: 0.28
Nodes (3): browser script, log_error(), main()

### Community 80 - "collaborate"
Cohesion: 0.36
Nodes (7): collaborate script, handle_merge_conflict(), log_error(), log_info(), log_step(), main(), verbose_echo()

### Community 81 - "figma-diff"
Cohesion: 0.42
Nodes (7): figma-diff script, log_error(), log_info(), log_step(), log_warn(), main(), show_help()

### Community 82 - "linux-setup"
Cohesion: 0.39
Nodes (6): linux-setup script, install_tool(), log_error(), log_step(), main(), verbose_echo()

### Community 83 - "mac-setup"
Cohesion: 0.39
Nodes (6): mac-setup script, install_tool(), log_error(), log_step(), main(), verbose_echo()

### Community 84 - "news-post"
Cohesion: 0.36
Nodes (7): news-post script, handle_merge_conflict(), log_error(), log_info(), log_step(), main(), verbose_echo()

### Community 85 - "news-read"
Cohesion: 0.36
Nodes (7): news-read script, handle_merge_conflict(), log_info(), log_step(), log_warn(), main(), verbose_echo()

### Community 86 - "principal-create"
Cohesion: 0.39
Nodes (6): principal-create script, log_error(), log_step(), main(), usage(), verbose_echo()

### Community 87 - "secret-migrate"
Cohesion: 0.33
Nodes (5): secret-migrate script, log_error(), log_step(), main(), verbose_echo()

### Community 88 - "session-archive"
Cohesion: 0.36
Nodes (6): session-archive script, log_error(), log_step(), main(), parse_args(), verbose_echo()

### Community 89 - "setup-agency"
Cohesion: 0.47
Nodes (8): setup-agency script, log_error(), log_info(), log_step(), log_warn(), main(), usage(), verbose_echo()

### Community 90 - "starter-update"
Cohesion: 0.42
Nodes (7): starter-update script, log_error(), log_step(), log_warn(), main(), usage(), verbose_echo()

### Community 91 - "gee_et_api.py"
Cohesion: 0.31
Nodes (8): _cache_key(), fetch_monthly_et(), fetch_season(), GEE OpenET Ensemble Plugin =========================== Fetches monthly ET from…, Fetch ET for a full growing season. Returns list of monthly results. Silently…, Attempt using earthengine-api if authenticated., Returns monthly ET in mm for a given lat/lon from GEE OpenET Ensemble. Uses on-…, _try_ee_python()

### Community 92 - "createSecretRoutes"
Cohesion: 0.39
Nodes (5): rowToAudit(), createSecretRoutes(), getAccessor(), ListAuditLogsQuery, SecretAuditLog

### Community 93 - "adhoc-log"
Cohesion: 0.43
Nodes (6): adhoc-log script, log_error(), log_step(), log_warn(), main(), verbose_echo()

### Community 94 - "agency-feedback"
Cohesion: 0.36
Nodes (4): agency-feedback script, log_error(), log_warn(), main()

### Community 95 - "agentname"
Cohesion: 0.32
Nodes (3): agentname script, main(), verbose_echo()

### Community 96 - "artifact-capture"
Cohesion: 0.43
Nodes (5): artifact-capture script, log_error(), log_warn(), main(), verbose_echo()

### Community 98 - "commit"
Cohesion: 0.46
Nodes (6): commit script, log_error(), log_step(), log_warn(), main(), verbose_echo()

### Community 99 - "commit-prefix"
Cohesion: 0.32
Nodes (3): commit-prefix script, main(), verbose_echo()

### Community 100 - "config"
Cohesion: 0.39
Nodes (5): config script, log_error(), log_step(), main(), verbose_echo()

### Community 101 - "context-review"
Cohesion: 0.39
Nodes (5): context-review script, log_error(), log_step(), main(), verbose_echo()

### Community 102 - "context-save"
Cohesion: 0.39
Nodes (5): context-save script, log_error(), log_step(), main(), verbose_echo()

### Community 103 - "dependencies-check"
Cohesion: 0.39
Nodes (5): dependencies-check script, log_error(), main(), usage(), verbose_echo()

### Community 104 - "epic-create"
Cohesion: 0.43
Nodes (5): epic-create script, log_error(), log_step(), main(), verbose_echo()

### Community 105 - "icloud-setup"
Cohesion: 0.39
Nodes (5): icloud-setup script, log_error(), log_step(), main(), verbose_echo()

### Community 106 - "instruction-capture"
Cohesion: 0.43
Nodes (5): instruction-capture script, log_error(), log_warn(), main(), verbose_echo()

### Community 107 - "instruction-complete"
Cohesion: 0.36
Nodes (4): instruction-complete script, log_error(), main(), verbose_echo()

### Community 108 - "instruction-index-update"
Cohesion: 0.32
Nodes (3): instruction-index-update script, main(), verbose_echo()

### Community 110 - "instruction-show"
Cohesion: 0.32
Nodes (3): instruction-show script, main(), verbose_echo()

### Community 111 - "iterm-setup"
Cohesion: 0.39
Nodes (5): iterm-setup script, log_error(), log_step(), main(), verbose_echo()

### Community 112 - "now"
Cohesion: 0.32
Nodes (3): now script, main(), verbose_echo()

### Community 113 - "principal"
Cohesion: 0.36
Nodes (4): principal script, log_warn(), main(), verbose_echo()

### Community 114 - "project-create"
Cohesion: 0.43
Nodes (6): project-create script, log_error(), log_info(), log_step(), main(), verbose_echo()

### Community 115 - "proposal-capture"
Cohesion: 0.36
Nodes (4): proposal-capture script, log_error(), main(), verbose_echo()

### Community 116 - "restore"
Cohesion: 0.36
Nodes (4): restore script, log_step(), main(), verbose_echo()

### Community 117 - "session-backup"
Cohesion: 0.39
Nodes (5): session-backup script, log_info(), log_step(), main(), verbose_echo()

### Community 118 - "sprint-create"
Cohesion: 0.43
Nodes (5): sprint-create script, log_error(), log_step(), main(), verbose_echo()

### Community 119 - "starter-cleanup"
Cohesion: 0.39
Nodes (5): starter-cleanup script, log_error(), log_step(), main(), verbose_echo()

### Community 120 - "starter-verify"
Cohesion: 0.36
Nodes (4): starter-verify script, log_error(), main(), verbose_echo()

### Community 121 - "tag"
Cohesion: 0.43
Nodes (5): tag script, log_error(), log_warn(), main(), verbose_echo()

### Community 122 - "test-run"
Cohesion: 0.39
Nodes (5): test-run script, log_error(), log_step(), log_warn(), main()

### Community 123 - "tool-version-add"
Cohesion: 0.39
Nodes (5): tool-version-add script, log_error(), log_info(), main(), verbose_echo()

### Community 124 - "version-bump"
Cohesion: 0.36
Nodes (4): version-bump script, log_info(), main(), verbose_echo()

### Community 125 - "welcomeback"
Cohesion: 0.32
Nodes (3): welcomeback script, log_info(), main()

### Community 126 - "whoami"
Cohesion: 0.32
Nodes (3): whoami script, main(), verbose_echo()

### Community 127 - "workstream"
Cohesion: 0.36
Nodes (4): workstream script, log_error(), main(), verbose_echo()

### Community 128 - "workstream-create"
Cohesion: 0.43
Nodes (5): workstream-create script, log_error(), log_step(), main(), verbose_echo()

### Community 129 - "gcp_function/main.py"
Cohesion: 0.36
Nodes (6): aquavolt_sync(), build_url(), compute_lai_fcover(), get_gspread_client(), GCP Cloud Function — triggered by Cloud Scheduler as HTTP POST., http

### Community 130 - "main"
Cohesion: 0.39
Nodes (5): compute_lai_fcover(), fetch_uncorrupted_indices(), main(), PIMLEngine, Fetches raw, uncorrupted, SCL-masked NDVI, NDWI and SAVI matrices from STAC…

### Community 131 - ".grantAccess"
Cohesion: 0.48
Nodes (3): rowToGrant(), GrantAccessRequest, SecretGrant

### Community 132 - "bench-build"
Cohesion: 0.48
Nodes (5): bench-build script, copy_dmg(), install_app(), show_version(), update_version()

### Community 134 - "agency-bench"
Cohesion: 0.67
Nodes (5): agency-bench script, ensure_built(), install_app(), launch_app(), write_pending_open()

### Community 135 - "ecostress_api.py"
Cohesion: 0.47
Nodes (5): _cache_key(), fetch_area(), _get_token(), ECOSTRESS NASA Plugin — Independent ET Validation (Area Task)…, Submit and retrieve an AppEEARS area sample request for ECOSTRESS ET.…

### Community 136 - "git-ci/install.sh"
Cohesion: 0.70
Nodes (4): log_info(), log_step(), log_warn(), install.sh script

### Community 137 - "nextjs-react/install.sh"
Cohesion: 0.60
Nodes (3): log_info(), log_step(), install.sh script

### Community 138 - "supabase/install.sh"
Cohesion: 0.70
Nodes (4): log_info(), log_step(), log_warn(), install.sh script

### Community 139 - "vercel/install.sh"
Cohesion: 0.70
Nodes (4): log_info(), log_step(), log_warn(), install.sh script

### Community 140 - "next.config.ts"
Cohesion: 0.40
Nodes (4): __dirname, __filename, nextConfig, packageJson

### Community 141 - "bugbench/page.tsx"
Cohesion: 0.40
Nodes (3): Bug, BugListResponse, STATUS_COLORS

### Community 142 - "review-spawn"
Cohesion: 0.70
Nodes (4): review-spawn script, generate_code_review_prompt(), generate_security_review_prompt(), generate_test_review_prompt()

### Community 144 - ".agency-starter/install.sh"
Cohesion: 0.83
Nodes (3): check_prereqs(), install_claude_code(), install.sh script

### Community 145 - "findings-consolidate"
Cohesion: 0.83
Nodes (3): findings-consolidate script, log_end(), show_help()

### Community 146 - "findings-save"
Cohesion: 0.83
Nodes (3): findings-save script, log_end(), show_help()

### Community 147 - "ensemble_fusion.py"
Cohesion: 0.83
Nodes (3): fetch_source(), fuse_data(), get_ensemble_optical()

### Community 148 - "generate_plots.py"
Cohesion: 0.83
Nodes (3): generate_baseline_plots(), generate_piml_plot(), main()

### Community 149 - "cimis_api.py"
Cohesion: 0.50
Nodes (3): fetch(), CIMIS API Ground-Truth Plugin ============================= Pulls real-time…, Fetches weather metrics from CIMIS. Falls back to Open-Meteo if blocked by DWR…

### Community 150 - "noaa_uscrn.py"
Cohesion: 0.50
Nodes (3): fetch(), NOAA USCRN Climate Reference Network Plugin…, Fetches hourly climate data from NOAA USCRN text files.

### Community 151 - "usda_scan.py"
Cohesion: 0.50
Nodes (3): fetch(), USDA SCAN Ground-Truth Soil Moisture Plugin…, Fetches real multi-depth soil moisture and temperature from USDA SCAN.

## Knowledge Gaps
- **199 isolated node(s):** `messages-check.sh script`, `session-end.sh script`, `session-start.sh script`, `statusline.sh script`, `__filename` (+194 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **50 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LSTMForecaster` connect `LSTMForecaster` to `api/main.py`, `TestPluginRegistry`, `test_aquavolt.py`, `TestStatistics`, `TestPIMLConstraints`, `TestDataPipeline`, `TestLSTMForecaster`, `TestFAO56Physics`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `createServiceLogger()` connect `logger.ts` to `LogRepository`, `.execute`, `idea.repository.ts`, `request.repository.ts`, `bug.repository.ts`, `message.repository.ts`, `DatabaseAdapter`, `TestConfigService`, `observation.service.ts`, `test-run.repository.ts`, `secret.service.ts`, `secret.repository.ts`, `secret-service/types.ts`, `auth.middleware.ts`, `SQLiteQueueAdapter`, `agency-service/src/index.ts`, `observation.repository.ts`, `QueueAdapter`, `test-runner.ts`, `test-service/types.ts`, `SecretService`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `DatabaseAdapter` connect `DatabaseAdapter` to `LogRepository`, `.execute`, `idea.repository.ts`, `observation.repository.ts`, `bug.repository.ts`, `QueueAdapter`, `request.repository.ts`, `SecretService`, `message.repository.ts`, `test-run.repository.ts`, `SecretRepository`, `secret.repository.ts`, `SQLiteAdapter`, `TestService`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **What connects `messages-check.sh script`, `session-end.sh script`, `session-start.sh script` to the rest of the system?**
  _199 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `LogRepository` be split into smaller, more focused modules?**
  _Cohesion score 0.0644384221619994 - nodes in this community are weakly interconnected._
- **Should `.execute` be split into smaller, more focused modules?**
  _Cohesion score 0.06583850931677018 - nodes in this community are weakly interconnected._
- **Should `idea.repository.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.07319347319347319 - nodes in this community are weakly interconnected._