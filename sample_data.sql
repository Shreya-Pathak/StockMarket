--Client is with ID 1 & Broker with ID 2
INSERT INTO market_stock VALUES(1, 'INFY', 10);
INSERT INTO market_stock VALUES(2, 'TCS', 10);
INSERT INTO market_stock VALUES(3, 'HCL', 10);

INSERT INTO market_exchange VALUES(1, 'NSE');
INSERT INTO market_exchange VALUES(2, 'BSE');

INSERT INTO market_indices VALUES(1, 'NIFTYTECH', 1);
INSERT INTO market_indices VALUES(2, 'BSETECH', 2);

INSERT INTO market_portfolio VALUES(1, 'TECH1', 1);
INSERT INTO market_portfolio VALUES(2, 'TECH2', 1);

INSERT INTO market_listedat VALUES(1, 1, 1);
INSERT INTO market_listedat VALUES(2, 1, 2);
INSERT INTO market_listedat VALUES(3, 1, 3);
INSERT INTO market_listedat VALUES(4, 2, 1);
INSERT INTO market_listedat VALUES(5, 2, 2);
INSERT INTO market_listedat VALUES(6, 2, 3);

INSERT INTO market_stockpricehistory VALUES(1, NOW(), 10, 1, 1);
INSERT INTO market_stockpricehistory VALUES(2, NOW(), 20, 1, 2);
INSERT INTO market_stockpricehistory VALUES(3, NOW(), 30, 1, 3);
INSERT INTO market_stockpricehistory VALUES(4, NOW(), 10, 2, 1);
INSERT INTO market_stockpricehistory VALUES(5, NOW(), 20, 2, 2);
INSERT INTO market_stockpricehistory VALUES(6, NOW(), 30, 2, 3);

INSERT INTO market_indexpricehistory VALUES(1, NOW(), 600, 1);
INSERT INTO market_indexpricehistory VALUES(2, NOW(), 600, 2);

INSERT INTO market_partofindex VALUES(1, 1, 1);
INSERT INTO market_partofindex VALUES(2, 1, 2);
INSERT INTO market_partofindex VALUES(3, 1, 3);
INSERT INTO market_partofindex VALUES(4, 2, 1);
INSERT INTO market_partofindex VALUES(5, 2, 2);
INSERT INTO market_partofindex VALUES(6, 2, 3);

INSERT INTO market_holdings VALUES(1, 100, 1000, 1, 1);
INSERT INTO market_holdings VALUES(2, 100, 2000, 1, 2); 
INSERT INTO market_holdings VALUES(3, 100, 3000, 1, 3);
INSERT INTO market_holdings VALUES(4, 50, 500, 2, 1);
INSERT INTO market_holdings VALUES(5, 50, 1000, 2, 2);
INSERT INTO market_holdings VALUES(6, 50, 1500, 2, 3);