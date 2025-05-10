CREATE TABLE IF NOT EXISTS fact_product_shoes (
    id               VARCHAR(36)   NOT NULL   PRIMARY KEY,
    title            VARCHAR(256)             NOT NULL,
    sub_title        VARCHAR(256),
    url              VARCHAR(512),
    image            VARCHAR(512),
    price_sale       DECIMAL(10,2),
    price_original   DECIMAL(10,2),
    gender           VARCHAR(128),      
    age_group        VARCHAR(32),

    brand            VARCHAR(64),
    dwid             VARCHAR(36),       
    year             INTEGER,
    month            INTEGER,
    day              INTEGER


)

DISTKEY(dwid)
SORTKEY(year, month, day);