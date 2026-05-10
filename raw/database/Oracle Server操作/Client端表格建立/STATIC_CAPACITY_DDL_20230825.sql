-- Start of DDL Script for Table GEMS.SC_COMBINE_DEMAND
-- Generated 2023-08-25 11:29:40 from GEMS@gems.world

-- Start of DDL Script for Table GEMS.SC_COMBINE_PRODUCT
-- Generated 2023-08-25 11:29:42 from GEMS@gems.world

CREATE TABLE sc_combine_product
    (site VARCHAR2(8 BYTE),
    product VARCHAR2(40 BYTE),
    combine_site VARCHAR2(8 BYTE),
    combine_product VARCHAR2(40 BYTE),
    combine_product_ratio NUMBER,
    update_user VARCHAR2(100 BYTE),
    update_time DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_COMBINE_PRODUCT

CREATE UNIQUE INDEX sc_combine_product_uidx ON sc_combine_product
  (
    site  ASC,
    product  ASC,
    combine_site  ASC,
    combine_product  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_COMBINE_PRODUCT

-- Start of DDL Script for Table GEMS.SC_COMBINE_PRODUCT_ADD
-- Generated 2023-08-25 11:29:42 from GEMS@gems.world

CREATE TABLE sc_combine_product_add
    (site VARCHAR2(8 BYTE),
    product VARCHAR2(40 BYTE),
    combine_site VARCHAR2(8 BYTE),
    combine_product VARCHAR2(40 BYTE),
    combine_product_ratio NUMBER,
    update_user VARCHAR2(100 BYTE),
    update_time DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_COMBINE_PRODUCT_ADD

CREATE UNIQUE INDEX sc_combine_product_add_uidx ON sc_combine_product_add
  (
    site  ASC,
    product  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_COMBINE_PRODUCT_ADD

-- Start of DDL Script for Table GEMS.SC_CROSS_ENTITY_MOVE_BACKUP
-- Generated 2023-08-25 11:29:44 from GEMS@gems.world

CREATE TABLE sc_cross_entity_move_backup
    (from_site VARCHAR2(10 BYTE),
    from_entity VARCHAR2(40 BYTE),
    from_type VARCHAR2(40 BYTE),
    from_recipe VARCHAR2(60 BYTE),
    from_geometry VARCHAR2(40 BYTE),
    from_group_id VARCHAR2(40 BYTE),
    from_product VARCHAR2(40 BYTE),
    from_process VARCHAR2(40 BYTE),
    from_reticlelayer VARCHAR2(40 BYTE),
    from_layer VARCHAR2(40 BYTE),
    from_stage VARCHAR2(40 BYTE),
    from_step VARCHAR2(40 BYTE),
    from_ppid_track VARCHAR2(40 BYTE),
    partgroup VARCHAR2(40 BYTE),
    to_site VARCHAR2(10 BYTE),
    to_entity VARCHAR2(40 BYTE),
    to_move_ratio NUMBER,
    to_entity_order NUMBER,
    contribution_date DATE,
    update_user VARCHAR2(100 BYTE),
    update_time DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     3145728
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_CROSS_ENTITY_MOVE_BACKUP

CREATE UNIQUE INDEX sc_cross_entity_move_bk_uidx ON sc_cross_entity_move_backup
  (
    from_site  ASC,
    from_entity  ASC,
    from_type  ASC,
    from_recipe  ASC,
    from_geometry  ASC,
    from_group_id  ASC,
    from_product  ASC,
    from_process  ASC,
    from_reticlelayer  ASC,
    from_layer  ASC,
    from_stage  ASC,
    from_step  ASC,
    from_ppid_track  ASC,
    partgroup  ASC,
    to_site  ASC,
    to_entity  ASC,
    contribution_date  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_CROSS_ENTITY_MOVE_BACKUP

-- Start of DDL Script for Table GEMS.SC_CROSS_ENTITY_TOOL_BK
-- Generated 2023-08-25 11:29:44 from GEMS@gems.world

CREATE TABLE sc_cross_entity_tool_bk
    (site VARCHAR2(8 BYTE),
    entity VARCHAR2(40 BYTE),
    priority NUMBER,
    backup_entity VARCHAR2(40 BYTE),
    unit_backup_number NUMBER,
    max_backup_number NUMBER,
    backup_efficiency_ratio NUMBER,
    contribution_date DATE,
    update_user VARCHAR2(100 BYTE),
    update_time DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_CROSS_ENTITY_TOOL_BK

CREATE UNIQUE INDEX sc_cross_entity_tool_bk_uidx ON sc_cross_entity_tool_bk
  (
    site  ASC,
    entity  ASC,
    priority  ASC,
    backup_entity  ASC,
    contribution_date  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     8388608
    NEXT        8388608
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_CROSS_ENTITY_TOOL_BK

-- Start of DDL Script for Table GEMS.SC_CROSS_ENTITY_TOOL_BK_RECORD
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_cross_entity_tool_bk_record
    (site VARCHAR2(8 BYTE),
    sc_project VARCHAR2(60 BYTE),
    case_name VARCHAR2(40 BYTE),
    wo_month DATE,
    entity VARCHAR2(40 BYTE),
    priority NUMBER,
    backup_entity VARCHAR2(40 BYTE),
    from_tool_number NUMBER,
    to_tool_number NUMBER,
    tier NUMBER,
    update_user VARCHAR2(100 BYTE),
    update_time DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_CROSS_ENTITY_TOOL_BK_RECORD

CREATE UNIQUE INDEX sc_cross_entity_tool_bk_rc_uid ON sc_cross_entity_tool_bk_record
  (
    site  ASC,
    sc_project  ASC,
    case_name  ASC,
    wo_month  ASC,
    entity  ASC,
    backup_entity  ASC,
    tier  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     8388608
    NEXT        8388608
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_CROSS_ENTITY_TOOL_BK_RECORD

-- Start of DDL Script for Table GEMS.SC_DEMAND_PRODUCTION
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_demand_production
    (source VARCHAR2(50 BYTE),
    demand_version VARCHAR2(50 BYTE),
    cbs_publish_time DATE,
    site VARCHAR2(10 BYTE),
    region VARCHAR2(50 BYTE),
    geometry VARCHAR2(80 BYTE),
    group_id VARCHAR2(50 BYTE),
    pdms_function VARCHAR2(80 BYTE),
    proj_name_revise VARCHAR2(30 BYTE),
    photo_layer NUMBER,
    ratio FLOAT(126),
    lta VARCHAR2(50 BYTE),
    product VARCHAR2(60 BYTE),
    process VARCHAR2(40 BYTE),
    processversion VARCHAR2(10 BYTE),
    case_name VARCHAR2(50 BYTE),
    wo_month DATE,
    wo_qty NUMBER,
    update_user VARCHAR2(100 BYTE),
    update_time DATE,
    wo_qty_last NUMBER,
    prd_layer VARCHAR2(30 BYTE),
    asp NUMBER,
    ref_group_id VARCHAR2(40 BYTE))
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_DEMAND_PRODUCTION

CREATE UNIQUE INDEX sc_demand_production_uidx ON sc_demand_production
  (
    demand_version  ASC,
    site  ASC,
    region  ASC,
    geometry  ASC,
    group_id  ASC,
    pdms_function  ASC,
    proj_name_revise  ASC,
    product  ASC,
    case_name  ASC,
    wo_month  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_DEMAND_PRODUCTION

-- Start of DDL Script for Table GEMS.SC_DEMAND_RD
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_demand_rd
    (source VARCHAR2(50 BYTE),
    rd_version VARCHAR2(50 BYTE),
    site VARCHAR2(10 BYTE),
    region VARCHAR2(50 BYTE),
    geometry VARCHAR2(80 BYTE),
    group_id VARCHAR2(50 BYTE),
    pdms_function VARCHAR2(80 BYTE),
    proj_name_revise VARCHAR2(30 BYTE),
    product VARCHAR2(60 BYTE),
    process VARCHAR2(40 BYTE),
    processversion VARCHAR2(10 BYTE),
    case_name VARCHAR2(50 BYTE),
    wo_month DATE,
    wo_qty NUMBER,
    update_user VARCHAR2(100 BYTE),
    update_time DATE,
    wo_qty_last NUMBER)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_DEMAND_RD

CREATE UNIQUE INDEX sc_demand_rd_uidx ON sc_demand_rd
  (
    rd_version  ASC,
    site  ASC,
    region  ASC,
    geometry  ASC,
    group_id  ASC,
    pdms_function  ASC,
    proj_name_revise  ASC,
    product  ASC,
    case_name  ASC,
    wo_month  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_DEMAND_RD

-- Start of DDL Script for Table GEMS.SC_ENTITY_UPPER_BOUND_LD
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_entity_upper_bound_ld
    (site VARCHAR2(8 BYTE),
    entity_group VARCHAR2(40 BYTE),
    upper_bound_loading NUMBER,
    update_user VARCHAR2(100 BYTE),
    update_time DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_ENTITY_UPPER_BOUND_LD

CREATE UNIQUE INDEX sc_entity_upper_bound_ld_uidx ON sc_entity_upper_bound_ld
  (
    site  ASC,
    entity_group  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_ENTITY_UPPER_BOUND_LD

-- Start of DDL Script for Table GEMS.SC_FLOW_ENTITY_ADD
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_flow_entity_add
    (site VARCHAR2(8 BYTE),
    entity VARCHAR2(40 BYTE),
    geometry VARCHAR2(40 BYTE),
    group_id VARCHAR2(40 BYTE),
    pdms_function VARCHAR2(40 BYTE),
    product VARCHAR2(40 BYTE),
    process VARCHAR2(40 BYTE),
    processversion VARCHAR2(40 BYTE),
    prcdsequence NUMBER,
    stepsequence NUMBER,
    prcd VARCHAR2(40 BYTE),
    step VARCHAR2(40 BYTE),
    stage VARCHAR2(40 BYTE),
    ppid VARCHAR2(50 BYTE),
    reticlelayer VARCHAR2(40 BYTE),
    layer VARCHAR2(40 BYTE),
    reticle_no VARCHAR2(40 BYTE),
    partgroup VARCHAR2(40 BYTE),
    steptitle VARCHAR2(100 BYTE),
    pre_eqptype VARCHAR2(40 BYTE),
    pre_ppid VARCHAR2(100 BYTE),
    pre2_eqptype VARCHAR2(40 BYTE),
    pre2_ppid VARCHAR2(100 BYTE),
    add_entity VARCHAR2(40 BYTE),
    pass NUMBER,
    contribution_date DATE,
    remark VARCHAR2(100 BYTE),
    update_user VARCHAR2(100 BYTE),
    update_time DATE,
    cd_spec NUMBER,
    capability VARCHAR2(40 BYTE))
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     6291456
    NEXT        2097152
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- End of DDL Script for Table GEMS.SC_FLOW_ENTITY_ADD

-- Start of DDL Script for Table GEMS.SC_FLOW_ENTITY_OVRD
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_flow_entity_ovrd
    (site VARCHAR2(8 BYTE),
    category VARCHAR2(20 BYTE),
    entity VARCHAR2(40 BYTE),
    geometry VARCHAR2(40 BYTE),
    group_id VARCHAR2(40 BYTE),
    pdms_function VARCHAR2(40 BYTE),
    product VARCHAR2(40 BYTE),
    process VARCHAR2(40 BYTE),
    processversion VARCHAR2(20 BYTE),
    prcdsequence NUMBER,
    stepsequence NUMBER,
    prcd VARCHAR2(40 BYTE),
    step VARCHAR2(40 BYTE),
    stage VARCHAR2(60 BYTE),
    ppid VARCHAR2(80 BYTE),
    reticlelayer VARCHAR2(40 BYTE),
    layer VARCHAR2(40 BYTE),
    reticle_no VARCHAR2(40 BYTE),
    partgroup VARCHAR2(40 BYTE),
    cd_upper NUMBER,
    cd_lower NUMBER,
    steptitle VARCHAR2(100 BYTE),
    pre_eqptype VARCHAR2(40 BYTE),
    pre_ppid VARCHAR2(100 BYTE),
    pre2_eqptype VARCHAR2(40 BYTE),
    pre2_ppid VARCHAR2(100 BYTE),
    override_entity VARCHAR2(40 BYTE),
    override_order NUMBER,
    contribution_date DATE,
    remark VARCHAR2(100 BYTE),
    update_user VARCHAR2(100 BYTE),
    update_time DATE,
    capability VARCHAR2(40 BYTE))
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- End of DDL Script for Table GEMS.SC_FLOW_ENTITY_OVRD

-- Start of DDL Script for Table GEMS.SC_FLOW_ENTITY_OVRD_ADD
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_flow_entity_ovrd_add
    (site VARCHAR2(8 BYTE),
    category VARCHAR2(20 BYTE),
    entity VARCHAR2(40 BYTE),
    geometry VARCHAR2(40 BYTE),
    group_id VARCHAR2(40 BYTE),
    pdms_function VARCHAR2(40 BYTE),
    product VARCHAR2(40 BYTE),
    process VARCHAR2(40 BYTE),
    processversion VARCHAR2(20 BYTE),
    prcdsequence NUMBER,
    stepsequence NUMBER,
    prcd VARCHAR2(40 BYTE),
    step VARCHAR2(40 BYTE),
    stage VARCHAR2(60 BYTE),
    ppid VARCHAR2(80 BYTE),
    reticlelayer VARCHAR2(40 BYTE),
    layer VARCHAR2(40 BYTE),
    reticle_no VARCHAR2(40 BYTE),
    partgroup VARCHAR2(40 BYTE),
    cd_upper NUMBER,
    cd_lower NUMBER,
    steptitle VARCHAR2(100 BYTE),
    pre_eqptype VARCHAR2(40 BYTE),
    pre_ppid VARCHAR2(100 BYTE),
    pre2_eqptype VARCHAR2(40 BYTE),
    pre2_ppid VARCHAR2(100 BYTE),
    override_entity VARCHAR2(40 BYTE),
    override_order NUMBER,
    contribution_date DATE,
    remark VARCHAR2(100 BYTE),
    update_user VARCHAR2(100 BYTE),
    update_time DATE,
    capability VARCHAR2(40 BYTE))
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- End of DDL Script for Table GEMS.SC_FLOW_ENTITY_OVRD_ADD

-- Start of DDL Script for Table GEMS.SC_LINE_YIELD_GEOMETRY
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_line_yield_geometry
    (site VARCHAR2(8 BYTE),
    geometry VARCHAR2(40 BYTE),
    start_date DATE,
    end_date DATE,
    line_yield_production FLOAT(126),
    line_yield_rd FLOAT(126),
    act_line_yield_production FLOAT(126),
    update_user VARCHAR2(100 BYTE),
    update_time DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_LINE_YIELD_GEOMETRY

CREATE UNIQUE INDEX sc_line_yield_geometry_uidx ON sc_line_yield_geometry
  (
    site  ASC,
    geometry  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_LINE_YIELD_GEOMETRY

-- Start of DDL Script for Table GEMS.SC_LINE_YIELD_PRODUCT
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_line_yield_product
    (site VARCHAR2(8 BYTE),
    product VARCHAR2(50 BYTE),
    start_date DATE,
    end_date DATE,
    line_yield_production FLOAT(126),
    line_yield_rd FLOAT(126),
    act_line_yield_production FLOAT(126),
    update_user VARCHAR2(100 BYTE),
    update_time DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_LINE_YIELD_PRODUCT

CREATE UNIQUE INDEX sc_line_yield_product_uidx ON sc_line_yield_product
  (
    site  ASC,
    product  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_LINE_YIELD_PRODUCT

-- Start of DDL Script for Table GEMS.SC_LINE_YIELD_SITE
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_line_yield_site
    (site VARCHAR2(8 BYTE),
    line_yield_production FLOAT(126),
    line_yield_rd FLOAT(126),
    act_line_yield_production FLOAT(126),
    update_user VARCHAR2(100 BYTE),
    update_time DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_LINE_YIELD_SITE

CREATE UNIQUE INDEX sc_line_yield_site_uidx ON sc_line_yield_site
  (
    site  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_LINE_YIELD_SITE

-- Start of DDL Script for Table GEMS.SC_LOADING
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_loading
    (plan_site VARCHAR2(10 BYTE),
    site VARCHAR2(10 BYTE),
    sc_project VARCHAR2(60 BYTE),
    case_name VARCHAR2(30 BYTE),
    wo_month DATE,
    entity VARCHAR2(40 BYTE),
    area VARCHAR2(40 BYTE),
    entity_group VARCHAR2(60 BYTE),
    tool_base VARCHAR2(20 BYTE),
    wph_flag VARCHAR2(20 BYTE),
    wpd_fix FLOAT(126),
    wpd_wpt FLOAT(126),
    demand_move FLOAT(126),
    non_demand_move FLOAT(126),
    auto_backup_move FLOAT(126),
    adj_move FLOAT(126),
    require_tool_number FLOAT(126),
    avail_tool_number FLOAT(126),
    auto_backup_number FLOAT(126),
    adj_tool FLOAT(126),
    retrofit FLOAT(126),
    new_buy FLOAT(126),
    before_loading FLOAT(126),
    after_loading FLOAT(126),
    surplus NUMBER,
    update_user VARCHAR2(20 BYTE),
    update_time DATE,
    entity_order NUMBER,
    upper_bound_loading NUMBER,
    uptime NUMBER,
    losstime NUMBER,
    batchloss NUMBER,
    wph NUMBER,
    wph_wpt NUMBER,
    dummy_move NUMBER,
    rework NUMBER,
    c_lot NUMBER)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     104857600
    NEXT        10485760
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_LOADING

CREATE UNIQUE INDEX sc_loading_uidx ON sc_loading
  (
    plan_site  ASC,
    site  ASC,
    sc_project  ASC,
    case_name  ASC,
    wo_month  ASC,
    entity  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     52428800
    NEXT        5242880
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_LOADING

-- Start of DDL Script for Table GEMS.SC_MEGA_FAB_PLANNING_VERSION
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_mega_fab_planning_version
    (site VARCHAR2(20 BYTE),
    sc_project VARCHAR2(100 BYTE),
    update_user VARCHAR2(20 BYTE),
    update_time DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_MEGA_FAB_PLANNING_VERSION

CREATE UNIQUE INDEX sc_mega_planning_ver_uidx ON sc_mega_fab_planning_version
  (
    site  ASC,
    sc_project  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_MEGA_FAB_PLANNING_VERSION

-- Start of DDL Script for Table GEMS.SC_MEGAFAB_FAB_VERSION_INFO
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_megafab_fab_version_info
    (mega_fab_plan VARCHAR2(50 BYTE),
    mega_fab_case_name VARCHAR2(50 BYTE),
    site VARCHAR2(20 BYTE),
    sc_project VARCHAR2(100 BYTE),
    case_name VARCHAR2(50 BYTE),
    wo_month DATE,
    megafab_run_user VARCHAR2(20 BYTE),
    megafab_start_run_datetime DATE,
    megafab_end_run_datetime DATE,
    megafab_result_confirm_user VARCHAR2(20 BYTE),
    megafab_result_confirm_datetm DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_MEGAFAB_FAB_VERSION_INFO

CREATE UNIQUE INDEX sc_megafab_fab_ver_info_uidx ON sc_megafab_fab_version_info
  (
    mega_fab_plan  ASC,
    mega_fab_case_name  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_MEGAFAB_FAB_VERSION_INFO

-- Start of DDL Script for Table GEMS.SC_PARAMETER_ACTUAL
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_parameter_actual
    (site VARCHAR2(8 BYTE),
    entity_ori VARCHAR2(40 BYTE),
    entity VARCHAR2(40 BYTE),
    act_dummy_move NUMBER,
    act_rework_reference NUMBER)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     6291456
    NEXT        2097152
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_PARAMETER_ACTUAL

CREATE UNIQUE INDEX sc_parameter_actual_uidx ON sc_parameter_actual
  (
    site  ASC,
    entity_ori  ASC,
    entity  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_PARAMETER_ACTUAL

-- Start of DDL Script for Table GEMS.SC_PRODFLOW_WPT
-- Generated 2023-08-25 11:29:45 from GEMS@gems.world

CREATE TABLE sc_prodflow_wpt
    (sc_project VARCHAR2(60 BYTE),
    case_name VARCHAR2(40 BYTE),
    wo_month DATE,
    site VARCHAR2(8 BYTE),
    geometry VARCHAR2(40 BYTE),
    group_id VARCHAR2(40 BYTE),
    pdms_function VARCHAR2(40 BYTE),
    product VARCHAR2(40 BYTE),
    process VARCHAR2(40 BYTE),
    processversion VARCHAR2(40 BYTE),
    combine_site VARCHAR2(8 BYTE),
    combine_product VARCHAR2(40 BYTE),
    prcdsequence NUMBER,
    stepsequence NUMBER,
    prcd VARCHAR2(40 BYTE),
    step VARCHAR2(40 BYTE),
    eqptype VARCHAR2(40 BYTE),
    stage VARCHAR2(40 BYTE),
    ppid VARCHAR2(50 BYTE),
    entity_ori VARCHAR2(40 BYTE),
    reticlelayer VARCHAR2(40 BYTE),
    layer VARCHAR2(40 BYTE),
    reticle_no VARCHAR2(40 BYTE),
    partgroup VARCHAR2(40 BYTE),
    cd_spec NUMBER,
    ppid_track VARCHAR2(50 BYTE),
    wpt NUMBER,
    wpt_from VARCHAR2(30 BYTE),
    steptitle VARCHAR2(100 BYTE),
    func_group VARCHAR2(30 BYTE),
    entity VARCHAR2(40 BYTE),
    entity_group VARCHAR2(60 BYTE),
    step_ratio NUMBER,
    pre_eqptype VARCHAR2(40 BYTE),
    pre_ppid VARCHAR2(100 BYTE),
    pre2_eqptype VARCHAR2(40 BYTE),
    pre2_ppid VARCHAR2(100 BYTE),
    wo_qty NUMBER,
    contribution_date DATE,
    update_time DATE,
    last_kscan_override VARCHAR2(40 BYTE),
    move NUMBER,
    line_yield NUMBER,
    category VARCHAR2(40 BYTE),
    apm_days NUMBER,
    capability VARCHAR2(40 BYTE))
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     209715200
    NEXT        20971520
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_PRODFLOW_WPT

CREATE INDEX sc_product_flow_wpt_idx ON sc_prodflow_wpt
  (
    sc_project  ASC,
    case_name  ASC,
    wo_month  ASC,
    combine_site  ASC,
    geometry  ASC,
    group_id  ASC,
    pdms_function  ASC,
    combine_product  ASC,
    process  ASC,
    processversion  ASC,
    prcdsequence  ASC,
    stepsequence  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     8388608
    NEXT        8388608
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/

CREATE UNIQUE INDEX sc_product_flow_wpt_uidx ON sc_prodflow_wpt
  (
    sc_project  ASC,
    case_name  ASC,
    wo_month  ASC,
    site  ASC,
    geometry  ASC,
    group_id  ASC,
    pdms_function  ASC,
    product  ASC,
    process  ASC,
    processversion  ASC,
    combine_site  ASC,
    combine_product  ASC,
    prcdsequence  ASC,
    stepsequence  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     8388608
    NEXT        8388608
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_PRODFLOW_WPT

-- Start of DDL Script for Table GEMS.SC_PRODUCT_FLOW_ADD
-- Generated 2023-08-25 11:29:46 from GEMS@gems.world

CREATE TABLE sc_product_flow_add
    (site VARCHAR2(8 BYTE),
    product VARCHAR2(40 BYTE),
    process VARCHAR2(40 BYTE),
    processversion VARCHAR2(40 BYTE),
    prcdsequence NUMBER,
    stepsequence NUMBER,
    prcd VARCHAR2(40 BYTE),
    step VARCHAR2(40 BYTE),
    eqptype VARCHAR2(40 BYTE),
    stage VARCHAR2(40 BYTE),
    ppid VARCHAR2(50 BYTE),
    entity VARCHAR2(40 BYTE),
    reticlelayer VARCHAR2(40 BYTE),
    layer VARCHAR2(40 BYTE),
    ppid_track VARCHAR2(50 BYTE),
    wpt NUMBER,
    steptitle VARCHAR2(100 BYTE),
    func_group VARCHAR2(100 BYTE),
    update_user VARCHAR2(100 BYTE),
    update_time DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     6291456
    NEXT        2097152
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_PRODUCT_FLOW_ADD

CREATE UNIQUE INDEX sc_product_flow_add_uidx ON sc_product_flow_add
  (
    site  ASC,
    product  ASC,
    process  ASC,
    processversion  ASC,
    prcdsequence  ASC,
    stepsequence  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     4194304
    NEXT        2097152
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_PRODUCT_FLOW_ADD

-- Start of DDL Script for Table GEMS.SC_SINGLE_FAB_BACKUP_RECORD
-- Generated 2023-08-25 11:29:46 from GEMS@gems.world

CREATE TABLE sc_single_fab_backup_record
    (from_site VARCHAR2(8 BYTE),
    sc_project VARCHAR2(60 BYTE),
    case_name VARCHAR2(40 BYTE),
    wo_month DATE,
    from_entity VARCHAR2(40 BYTE),
    from_type VARCHAR2(40 BYTE),
    from_recipe VARCHAR2(50 BYTE),
    from_geometry VARCHAR2(40 BYTE),
    from_group_id VARCHAR2(40 BYTE),
    from_product VARCHAR2(40 BYTE),
    from_process VARCHAR2(40 BYTE),
    from_reticlelayer VARCHAR2(40 BYTE),
    from_layer VARCHAR2(40 BYTE),
    from_stage VARCHAR2(40 BYTE),
    from_step VARCHAR2(40 BYTE),
    from_ppid_track VARCHAR2(50 BYTE),
    to_site VARCHAR2(8 BYTE),
    to_entity VARCHAR2(40 BYTE),
    to_move_ratio NUMBER,
    contribution_date DATE,
    qty NUMBER,
    update_user VARCHAR2(100 BYTE),
    update_time DATE,
    remark VARCHAR2(200 BYTE))
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     104857600
    NEXT        5242880
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- End of DDL Script for Table GEMS.SC_SINGLE_FAB_BACKUP_RECORD

-- Start of DDL Script for Table GEMS.SC_SINGLE_FAB_PLANNING_VERSION
-- Generated 2023-08-25 11:29:46 from GEMS@gems.world

CREATE TABLE sc_single_fab_planning_version
    (site VARCHAR2(10 BYTE),
    sc_project VARCHAR2(100 BYTE),
    update_user VARCHAR2(20 BYTE),
    update_time DATE)
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_SINGLE_FAB_PLANNING_VERSION

CREATE UNIQUE INDEX sc_sin_fab_planning_ver_uidx ON sc_single_fab_planning_version
  (
    site  ASC,
    sc_project  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_SINGLE_FAB_PLANNING_VERSION

-- Start of DDL Script for Table GEMS.SC_SINGLE_FAB_VERSION_INFO
-- Generated 2023-08-25 11:29:46 from GEMS@gems.world

CREATE TABLE sc_single_fab_version_info
    (site VARCHAR2(10 BYTE),
    sc_project VARCHAR2(100 BYTE),
    case_name VARCHAR2(50 BYTE),
    wo_month DATE,
    demand_source VARCHAR2(20 BYTE),
    demand_version VARCHAR2(60 BYTE),
    rd_source VARCHAR2(20 BYTE),
    rd_version VARCHAR2(60 BYTE),
    capacity_version VARCHAR2(30 BYTE),
    demand_ready_user VARCHAR2(20 BYTE),
    demand_ready_date_time DATE,
    capacity_ready_user VARCHAR2(20 BYTE),
    capacity_ready_date_time DATE,
    start_run_user VARCHAR2(20 BYTE),
    start_run_date_time DATE,
    result_submit_user VARCHAR2(20 BYTE),
    result_submit_date_time DATE,
    megafab_run_user VARCHAR2(20 BYTE),
    megafab_run_date_time DATE,
    sc_project_fix VARCHAR2(20 BYTE),
    sc_project_official VARCHAR2(20 BYTE),
    apm_days NUMBER,
    end_run_date_time DATE,
    is_processed VARCHAR2(20 BYTE))
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_SINGLE_FAB_VERSION_INFO

CREATE UNIQUE INDEX sc_single_fab_ver_info_uidx ON sc_single_fab_version_info
  (
    site  ASC,
    sc_project  ASC,
    case_name  ASC,
    wo_month  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_SINGLE_FAB_VERSION_INFO

-- Start of DDL Script for Table GEMS.SC_TECH_GROUP
-- Generated 2023-08-25 11:29:46 from GEMS@gems.world

CREATE TABLE sc_tech_group
    (wafersize NUMBER,
    geometry VARCHAR2(80 BYTE),
    pdms_function VARCHAR2(80 BYTE),
    tech_order NUMBER,
    geo_func VARCHAR2(80 BYTE),
    geo_func_group VARCHAR2(80 BYTE))
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     2097152
    NEXT        1048576
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/



-- Start of DDL Script for Table GEMS.SC_ENTITY_CAPA_PARAMETER
-- Generated 2023-08-25 11:31:00 from GEMS@gems.world

CREATE TABLE sc_entity_capa_parameter
    (capacity_version VARCHAR2(30 BYTE),
    site VARCHAR2(8 BYTE),
    entity VARCHAR2(40 BYTE),
    area VARCHAR2(20 BYTE),
    entity_group VARCHAR2(40 BYTE),
    tool_base VARCHAR2(20 BYTE),
    wpd NUMBER,
    wph NUMBER,
    wph_flag VARCHAR2(20 BYTE),
    uptime NUMBER,
    losstime NUMBER,
    batchloss NUMBER,
    avail_tool_number NUMBER,
    dummy_move NUMBER,
    rework NUMBER,
    c_lot NUMBER,
    per_eq_chamber_number NUMBER,
    contribution_date DATE,
    update_user VARCHAR2(100 BYTE),
    update_time DATE,
    entity_order VARCHAR2(20 BYTE))
  SEGMENT CREATION IMMEDIATE
  PCTFREE     10
  INITRANS    1
  MAXTRANS    255
  TABLESPACE  gems_dat3
  STORAGE   (
    INITIAL     62914560
    NEXT        6291456
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
  NOCACHE
  MONITORING
  NOPARALLEL
  LOGGING
/





-- Indexes for SC_ENTITY_CAPA_PARAMETER

CREATE UNIQUE INDEX sc_entity_capa_parameter_uidx ON sc_entity_capa_parameter
  (
    capacity_version  ASC,
    site  ASC,
    entity  ASC,
    contribution_date  ASC
  )
  PCTFREE     10
  INITRANS    2
  MAXTRANS    255
  TABLESPACE  gems_dat4
  STORAGE   (
    INITIAL     8388608
    NEXT        8388608
    PCTINCREASE 0
    MINEXTENTS  1
    MAXEXTENTS  2147483645
  )
NOPARALLEL
NOLOGGING
/



-- End of DDL Script for Table GEMS.SC_ENTITY_CAPA_PARAMETER



-- End of DDL Script for Table GEMS.SC_TECH_GROUP

