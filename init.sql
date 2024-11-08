CREATE TABLE IF NOT EXISTS user_analytics (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    mac_address VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    usage_time INTERVAL NOT NULL,   
    upload FLOAT NOT NULL,
    download FLOAT NOT NULL
);
