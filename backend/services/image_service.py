"""
Image service for UK-only image selection.
"""
import re
import random
import logging
from typing import Set, Optional

logger = logging.getLogger(__name__)

# CHESHIRE LOCATION-SPECIFIC IMAGES 
LOCATION_IMAGES = {
    'knutsford': [
        'https://images.unsplash.com/photo-1591027590129-4de51a2fb3f6?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&h=500&fit=crop',
    ],
    'wilmslow': [
        'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1565008576549-57569a49371d?w=800&h=500&fit=crop',
    ],
    'alderley': [
        'https://images.unsplash.com/photo-1588152850700-c82ecb8ba9b1?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1566159196936-b4f3dc52dbfc?w=800&h=500&fit=crop',
    ],
    'prestbury': [
        'https://images.unsplash.com/photo-1670620800086-3b9a345967fc?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1670620800060-b90889e9f7d9?w=800&h=500&fit=crop',
    ],
    'chester': [
        'https://images.unsplash.com/photo-1590058175032-5e68d70e3e2b?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1567610018053-7f1b5c2d7f01?w=800&h=500&fit=crop',
    ],
    'macclesfield': [
        'https://images.unsplash.com/photo-1763238638505-76f22e816560?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1696113073939-213d3d9610b1?w=800&h=500&fit=crop',
    ],
    'golden triangle': [
        'https://images.unsplash.com/photo-1508325739122-c57a76313bf4?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1524919131051-b29c762a8356?w=800&h=500&fit=crop',
    ],
}

# UK-ONLY CATEGORY IMAGES
CATEGORY_IMAGES = {
    'Local News': [
        'https://images.unsplash.com/photo-1591027590129-4de51a2fb3f6?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1650117790243-d659112e532c?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1588152850700-c82ecb8ba9b1?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1568190538421-53523065d4b8?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1670620800086-3b9a345967fc?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1670620800060-b90889e9f7d9?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1567610018053-7f1b5c2d7f01?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1590058175032-5e68d70e3e2b?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1566159196936-b4f3dc52dbfc?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1599974331560-c4d5c209a005?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1590182844668-a09d1fa27c1f?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1584530782379-886b08e3c9b5?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1542566604-6d30ead97cfe?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1565008576549-57569a49371d?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1527489377706-5bf97e608852?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1508325739122-c57a76313bf4?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1549544131-35406370c265?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1524919131051-b29c762a8356?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1763238638505-76f22e816560?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1696113073939-213d3d9610b1?w=800&h=500&fit=crop',
    ],
    'Business': [
        'https://images.unsplash.com/photo-1486325212027-8081e485255e?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1529655683826-aba9b3e77383?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1520986606214-8b456906c813?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1454117096348-e4abbeba002c?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1526129318478-62ed807ebdf9?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1560179707-f14e90ef3623?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1521737711867-e3b97375f902?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=800&h=500&fit=crop',
    ],
    'Tech': [
        'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1535378620166-273708d44e4c?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1547658719-da2b51169166?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1555255707-c07966088b7b?w=800&h=500&fit=crop',
    ],
    'Finance': [
        'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1559526324-4b87b5e36e44?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1460472178825-e5240623afd5?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1565372195458-9de0b320ef04?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1621761191319-c6fb62004040?w=800&h=500&fit=crop',
    ],
    'Health': [
        'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1571772996211-2f02c9727629?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1551076805-e1869033e561?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1584432810601-6c7f27d2362b?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1581594693702-fbdc51b2763b?w=800&h=500&fit=crop',
    ],
    'Weather': [
        'https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1478719059408-592965723cbc?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1500740516770-92bd004b996e?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1428592953211-077101b2021b?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1527482797697-8795b05a13fe?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1530908295418-a12e326966ba?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1561553590-267fc716698a?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1605451523461-b48c9d0ec3c9?w=800&h=500&fit=crop',
    ],
    'Food': [
        'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1473093295043-cdd812d0e601?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800&h=500&fit=crop',
    ],
    'Festive': [
        'https://images.unsplash.com/photo-1512389142860-9c449e58a543?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1482517967863-00e15c9b44be?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1543589077-47d81606c1bf?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1576919228236-a097c32a5cd4?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1544986581-efac024faf62?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1512909006721-3d6018887383?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1481653125770-b78c206c59d4?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1511407192727-02e0a49e8a0f?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1607447009832-c18dafe4b61b?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1513297887119-d46091b24bfa?w=800&h=500&fit=crop',
    ],
    'Events': [
        'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1506157786151-b8491531f063?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1464047736614-af63643285bf?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1472653431158-6364773b2a56?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1492538368677-f6e0afe31dcc?w=800&h=500&fit=crop',
    ],
    'Sports': [
        'https://images.unsplash.com/photo-1459865264687-595d652de67e?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1530549387789-4c1017266635?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1535131749006-b7f58c99034b?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=800&h=500&fit=crop',
    ],
    'Community': [
        'https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1559027615-cd4628902d4a?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1511285560929-80b456fea0bc?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1491438590914-bc09fcaaf77a?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1528605248644-14dd04022da1?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=800&h=500&fit=crop',
    ],
    'UK News': [
        'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1529655683826-aba9b3e77383?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1486325212027-8081e485255e?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1520986606214-8b456906c813?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1454117096348-e4abbeba002c?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1526129318478-62ed807ebdf9?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1485201543483-f06c8d2a8fb4?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1505092670810-fb7d4ff03ee5?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1508966319062-b5bc8fb46d38?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=800&h=500&fit=crop',
    ]
}

# TOPIC-SPECIFIC IMAGE MAPPINGS
TOPIC_IMAGE_MAPPINGS = {
    'police': [
        'https://images.unsplash.com/photo-1455735459330-969b65c65b1c?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1595329088732-d853e3ceba74?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1453873531674-2151bcd01707?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1532375810709-75b1da00537c?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1594312915251-48db9280c8f1?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1569863959165-56dae551d4fc?w=800&h=500&fit=crop',
    ],
    'crime': [
        'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1505664194779-8beaceb93744?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1453873531674-2151bcd01707?w=800&h=500&fit=crop',
    ],
    'arrest': [
        'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1453873531674-2151bcd01707?w=800&h=500&fit=crop',
    ],
    'court': [
        'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1505664194779-8beaceb93744?w=800&h=500&fit=crop',
    ],
    'fire': [
        'https://images.unsplash.com/photo-1486551937199-baf066858de7?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1517213849290-bbbfffdc6da3?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1560635070-c7d8e83e1a71?w=800&h=500&fit=crop',
    ],
    'crash': [
        'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800&h=500&fit=crop',
    ],
    'motorway': [
        'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800&h=500&fit=crop',
    ],
    'nhs': [
        'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=800&h=500&fit=crop',
    ],
    'hospital': [
        'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1516549655169-df83a0774514?w=800&h=500&fit=crop',
    ],
    'school': [
        'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=800&h=500&fit=crop',
    ],
    'transport': [
        'https://images.unsplash.com/photo-1517355163-39cc70762df7?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800&h=500&fit=crop',
    ],
    'train': [
        'https://images.unsplash.com/photo-1517355163-39cc70762df7?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1474487548417-781cb71495f3?w=800&h=500&fit=crop',
    ],
    'weather': [
        'https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1561553590-267fc716698a?w=800&h=500&fit=crop',
    ],
    'council': [
        'https://images.unsplash.com/photo-1555848962-6e79363ec58f?w=800&h=500&fit=crop',
        'https://images.unsplash.com/photo-1577495508048-b635879837f1?w=800&h=500&fit=crop',
    ]
}

# CHESHIRE FALLBACK IMAGES
CHESHIRE_FALLBACK_IMAGES = [
    'https://images.unsplash.com/photo-1549544131-35406370c265?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1568190538421-53523065d4b8?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1508325739122-c57a76313bf4?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1599974331560-c4d5c209a005?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1590182844668-a09d1fa27c1f?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1524919131051-b29c762a8356?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1696113073939-213d3d9610b1?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1566159196936-b4f3dc52dbfc?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1588152850700-c82ecb8ba9b1?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1542566604-6d30ead97cfe?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1565008576549-57569a49371d?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1527489377706-5bf97e608852?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1591027590129-4de51a2fb3f6?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1570193628474-5ba0c21b8f3f?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1500343673619-3aa6d5c281c1?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1582555172866-f73bb12a2ab3?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1516815231560-8f41ec531527?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1548013146-72479768bada?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1502139214982-d0ad755818d8?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1518378188025-22bd89516ee2?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1568084680786-a84f91d1153c?w=800&h=500&fit=crop',
    'https://images.unsplash.com/photo-1598513431456-ebedfd60c98f?w=800&h=500&fit=crop',
]

# BANNED IMAGES
BANNED_IMAGES = [
    'https://images.unsplash.com/photo-1504711434969-e33886168f5c',
    'https://images.unsplash.com/photo-1586339949916-3e9457bef6d3',
    'https://images.unsplash.com/photo-1566378246598-5b11a0d486cc',
    'https://images.unsplash.com/photo-1595152772835-219674b2a8a6',
    'https://images.unsplash.com/photo-1523995462485-3d171b5c8fa9',
    'https://images.unsplash.com/photo-1584820927498-cfe5211fd8bf',
    'https://images.unsplash.com/photo-1553484771-047a44eee27b',
    'https://images.unsplash.com/photo-1560179707-f14e90ef3623',
]


def get_all_unique_images():
    """Get all unique images from all categories"""
    all_images = set()
    for images in CATEGORY_IMAGES.values():
        all_images.update(images)
    return list(all_images)


ALL_UNIQUE_IMAGES = get_all_unique_images()


def extract_photo_id(url: str) -> str:
    """Extract the unique photo ID from an image URL."""
    if not url:
        return ""
    
    if 'unsplash.com' in url or 'photo-' in url:
        match = re.search(r'photo-([a-zA-Z0-9_-]+)', url)
        if match:
            return f'unsplash:{match.group(0)}'
    
    if 'pexels.com' in url:
        match = re.search(r'/photos/(\d+)', url)
        if match:
            return f'pexels:{match.group(1)}'
        match = re.search(r'pexels-photo-(\d+)', url)
        if match:
            return f'pexels:{match.group(1)}'
    
    if 'pixabay.com' in url:
        match = re.search(r'[_-](\d{5,})', url)
        if match:
            return f'pixabay:{match.group(1)}'
    
    base_url = url.split('?')[0]
    return base_url


def is_image_used(url: str, used_photo_ids: Set[str]) -> bool:
    """Check if an image is already used."""
    photo_id = extract_photo_id(url)
    return photo_id in used_photo_ids


def add_image_to_used(url: str, used_photo_ids: Set[str]) -> None:
    """Add an image's photo ID to the used set."""
    photo_id = extract_photo_id(url)
    if photo_id:
        used_photo_ids.add(photo_id)


async def get_used_images_from_db(db) -> Set[str]:
    """Fetch all currently used photo IDs from the database."""
    try:
        articles = await db.articles.find({}, {"image": 1, "_id": 0}).to_list(1000)
        used_photo_ids = set()
        for art in articles:
            if 'image' in art and art['image']:
                photo_id = extract_photo_id(art['image'])
                if photo_id:
                    used_photo_ids.add(photo_id)
        return used_photo_ids
    except Exception as e:
        logger.error(f"Error fetching used images: {str(e)}")
        return set()


def select_location_image(title: str, content: str, used_photo_ids: Set[str]) -> Optional[str]:
    """Select a UK image that matches the article's location if possible."""
    text = (title + ' ' + content).lower()
    
    location_matches = []
    for location, images in LOCATION_IMAGES.items():
        if location in text:
            available = [
                img for img in images 
                if not is_image_used(img, used_photo_ids)
                and not any(b in img for b in BANNED_IMAGES)
            ]
            if available:
                location_matches.extend(available)
    
    if location_matches:
        image = random.choice(location_matches)
        logger.info(f"Selected location-specific UK image: {image[-50:]}")
        return image
    
    return None


def select_topic_image(title: str, content: str, used_photo_ids: Set[str]) -> Optional[str]:
    """Select a specific topic-based image if keywords match."""
    text = (title + ' ' + content).lower()
    
    for topic, images in TOPIC_IMAGE_MAPPINGS.items():
        if topic in text:
            available = [
                img for img in images 
                if not is_image_used(img, used_photo_ids)
                and not any(b in img for b in BANNED_IMAGES)
            ]
            if available:
                image = random.choice(available)
                logger.info(f"Selected TOPIC-specific image for '{topic}': {image[-50:]}")
                return image
    return None


def select_unique_image(category: str, used_photo_ids: Set[str], title: str = "", content: str = "") -> Optional[str]:
    """STRICT unique UK-only image selection."""
    if title or content:
        topic_image = select_topic_image(title, content, used_photo_ids)
        if topic_image:
            return topic_image

    if title or content:
        location_image = select_location_image(title, content, used_photo_ids)
        if location_image:
            return location_image
    
    category_images = CATEGORY_IMAGES.get(category, [])
    available = [
        img for img in category_images 
        if not is_image_used(img, used_photo_ids)
        and not any(b in img for b in BANNED_IMAGES)
    ]
    
    if available:
        image = random.choice(available)
        logger.info(f"Selected unique UK {category} image: {image[-50:]}")
        return image
    
    fallback_pool = ALL_UNIQUE_IMAGES
    if title and ('cheshire' in title.lower() or 'golden triangle' in title.lower() or 'knutsford' in title.lower() or 'wilmslow' in title.lower()):
        fallback_pool = CHESHIRE_FALLBACK_IMAGES + CATEGORY_IMAGES.get('Local News', [])
        
    all_available = [
        img for img in fallback_pool
        if not is_image_used(img, used_photo_ids)
        and not any(b in img for b in BANNED_IMAGES)
    ]
    
    if all_available:
        image = random.choice(all_available)
        logger.info(f"Selected unique fallback image from pool: {image[-50:]}")
        return image
    
    logger.warning(f"No unique UK images available! {len(used_photo_ids)} images already in use")
    return None


async def get_dynamic_image(
    title: str, 
    category: str, 
    content: str, 
    scope: str, 
    used_photo_ids: Set[str],
    unsplash_service,
    pexels_service,
    pixabay_service
) -> Optional[str]:
    """Get an image for an article using multiple free image APIs."""
    if used_photo_ids is None:
        used_photo_ids = set()
    
    # Try Unsplash API first
    if unsplash_service.enabled:
        try:
            unsplash_image = await unsplash_service.get_article_image(
                title=title,
                category=category,
                content=content,
                scope=scope,
                used_images=used_photo_ids
            )
            if unsplash_image and not is_image_used(unsplash_image, used_photo_ids):
                logger.info(f"✅ Unsplash UK image matched for: {title[:40]}...")
                return unsplash_image
        except Exception as e:
            logger.warning(f"Unsplash API error: {str(e)}")
    
    # Try Pexels API second
    if pexels_service.enabled:
        try:
            pexels_image = await pexels_service.get_article_image(
                title=title,
                category=category,
                scope=scope,
                used_images=used_photo_ids
            )
            if pexels_image and not is_image_used(pexels_image, used_photo_ids):
                logger.info(f"✅ Pexels UK image matched for: {title[:40]}...")
                return pexels_image
        except Exception as e:
            logger.warning(f"Pexels API error: {str(e)}")
    
    # Try Pixabay API third
    if pixabay_service.enabled:
        try:
            pixabay_image = await pixabay_service.get_article_image(
                title=title,
                category=category,
                scope=scope,
                used_images=used_photo_ids
            )
            if pixabay_image and not is_image_used(pixabay_image, used_photo_ids):
                logger.info(f"✅ Pixabay UK image matched for: {title[:40]}...")
                return pixabay_image
        except Exception as e:
            logger.warning(f"Pixabay API error: {str(e)}")
    
    # Fallback to static pool
    static_image = select_unique_image(category, used_photo_ids, title, content)
    if static_image:
        logger.info(f"Using static pool image for: {title[:40]}...")
    return static_image
