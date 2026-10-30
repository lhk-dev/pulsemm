"""Pre-configured 180 prestigious RSS feeds across 10 categories (18 sources per category)."""

from typing import TypedDict


class FeedSource(TypedDict):
    name: str
    url: str


FEEDS_CONFIG: dict[str, list[FeedSource]] = {
    "Myanmar": [
        {
            "name": "The Irrawaddy",
            "url": "https://www.irrawaddy.com/feed",
        },
        {
            "name": "Myanmar Now",
            "url": "https://myanmar-now.org/en/feed/",
        },
        {
            "name": "Mizzima News",
            "url": "https://eng.mizzima.com/feed",
        },
        {
            "name": "Frontier Myanmar",
            "url": "https://www.frontiermyanmar.net/en/feed/",
        },
        {
            "name": "BNI Myanmar Peace Monitor",
            "url": "https://www.bnionline.net/en/feed",
        },
        {
            "name": "DVB (Democratic Voice of Burma)",
            "url": "https://english.dvb.no/feed/",
        },
        {
            "name": "Reuters (Myanmar Coverage)",
            "url": "https://news.google.com/rss/search?q=site:reuters.com+Myanmar&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Nikkei Asia (Myanmar Coverage)",
            "url": "https://news.google.com/rss/search?q=site:asia.nikkei.com+Myanmar&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "BBC & AP (Myanmar Coverage)",
            "url": "https://news.google.com/rss/search?q=(site:bbc.com+OR+site:apnews.com)+Myanmar+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "SCMP & CNA (Myanmar & Regional)",
            "url": "https://news.google.com/rss/search?q=(site:scmp.com+OR+site:channelnewsasia.com)+Myanmar+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Crisis Group & USIP (Myanmar Analysis)",
            "url": "https://news.google.com/rss/search?q=(site:crisisgroup.org+OR+site:usip.org+OR+site:thediplomat.com)+Myanmar&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "World Bank, ADB & UN Myanmar Reports",
            "url": "https://news.google.com/rss/search?q=Myanmar+(%22World+Bank%22+OR+%22Asian+Development+Bank%22+OR+UNDP+OR+ASEAN)+economy+OR+development&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Myanmar Business, Economy & Market",
            "url": "https://news.google.com/rss/search?q=Myanmar+(business+OR+economy+OR+kyat+OR+gold+OR+trade+OR+banking+OR+investment+OR+market)+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Myanmar Opportunities, Jobs & Scholarships",
            "url": "https://news.google.com/rss/search?q=Myanmar+(opportunity+OR+scholarship+OR+fellowship+OR+startup+OR+jobs+OR+digital+OR+entrepreneur+OR+youth)+when:14d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Myanmar Politics & Current Situation",
            "url": "https://news.google.com/rss/search?q=Myanmar+(politics+OR+situation+OR+junta+OR+SAC+OR+NUG+OR+PDF+OR+election+OR+conscription)+when:3d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Myanmar Ethnic States & Ground Situation",
            "url": "https://news.google.com/rss/search?q=Myanmar+(Rakhine+OR+Arakan+OR+Kachin+OR+Shan+OR+Karen+OR+Chin+OR+Sagaing+OR+Lashio+OR+Myawaddy)+when:3d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Myanmar Border Trade & Regional Ties",
            "url": "https://news.google.com/rss/search?q=Myanmar+(border+OR+export+OR+import+OR+Thailand+OR+China+OR+Singapore+OR+India+OR+ASEAN)+when:5d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Yangon, Mandalay & Domestic Situation",
            "url": "https://news.google.com/rss/search?q=(Yangon+OR+Mandalay+OR+Naypyidaw)+Myanmar+when:3d&hl=en-US&gl=US&ceid=US:en",
        },
    ],
    "World Crises & Geopolitics": [
        {
            "name": "Foreign Affairs (CFR)",
            "url": "https://www.foreignaffairs.com/rss.xml",
        },
        {
            "name": "Foreign Policy Magazine",
            "url": "https://foreignpolicy.com/feed/",
        },
        {
            "name": "The Economist (International)",
            "url": "https://www.economist.com/international/rss.xml",
        },
        {
            "name": "Financial Times (World & Geopolitics)",
            "url": "https://www.ft.com/world?format=rss",
        },
        {
            "name": "Reuters World Geopolitics",
            "url": "https://news.google.com/rss/search?q=site:reuters.com+(war+OR+iran+OR+ukraine+OR+taiwan+OR+china+OR+nato+OR+sanctions+OR+missile)+when:2d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Associated Press (AP) Global Crises",
            "url": "https://news.google.com/rss/search?q=site:apnews.com+(war+OR+iran+OR+israel+OR+ukraine+OR+russia+OR+china+OR+taiwan+OR+nuclear)+when:2d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "New York Times World",
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        },
        {
            "name": "Washington Post World",
            "url": "https://feeds.washingtonpost.com/rss/world",
        },
        {
            "name": "Wall Street Journal World",
            "url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
        },
        {
            "name": "Council on Foreign Relations (CFR)",
            "url": "https://news.google.com/rss/search?q=site:cfr.org+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Chatham House & Carnegie Endowment",
            "url": "https://news.google.com/rss/search?q=(site:chathamhouse.org+OR+site:carnegieendowment.org)+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "International Crisis Group",
            "url": "https://www.crisisgroup.org/rss.xml",
        },
        {
            "name": "The Diplomat (Indo-Pacific Security)",
            "url": "https://thediplomat.com/feed/",
        },
        {
            "name": "Nikkei Asia & SCMP Geopolitics",
            "url": "https://news.google.com/rss/search?q=(site:asia.nikkei.com+OR+site:scmp.com)+(China+OR+Taiwan+OR+US+OR+military+OR+sanctions+OR+ASEAN)+when:2d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Iran, Israel & Middle East War Watch",
            "url": "https://news.google.com/rss/search?q=(Iran+OR+Israel+OR+Gaza+OR+Lebanon+OR+Red+Sea)+(war+OR+airstrike+OR+missile+OR+nuclear+OR+military+OR+retaliation)+when:2d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Russia-Ukraine & NATO War Watch",
            "url": "https://news.google.com/rss/search?q=(Ukraine+AND+Russia)+(war+OR+missile+OR+offensive+OR+NATO+OR+sanctions+OR+ceasefire+OR+frontline)+when:2d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "US-China & Taiwan Strait Flashpoints",
            "url": "https://news.google.com/rss/search?q=(China+AND+(US+OR+Taiwan+OR+%22South+China+Sea%22))+(military+OR+sanctions+OR+tariffs+OR+blockade+OR+security)+when:3d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "North Korea & Nuclear Deterrence Watch",
            "url": "https://news.google.com/rss/search?q=(%22North+Korea%22+OR+ICBM+OR+%22nuclear+weapons%22+OR+%22uranium+enrichment%22+OR+%22Strait+of+Hormuz%22)+when:3d&hl=en-US&gl=US&ceid=US:en",
        },
    ],
    "Military, Weapons & Defense Tech": [
        {
            "name": "The War Zone (TWZ)",
            "url": "https://www.twz.com/feed",
        },
        {
            "name": "Breaking Defense",
            "url": "https://breakingdefense.com/feed/",
        },
        {
            "name": "Defense One",
            "url": "https://www.defenseone.com/rss/all/",
        },
        {
            "name": "Defense News (Global Warfare & Weapons)",
            "url": "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml",
        },
        {
            "name": "USNI News (US Naval Institute)",
            "url": "https://news.usni.org/feed",
        },
        {
            "name": "Air & Space Forces Magazine",
            "url": "https://www.airandspaceforces.com/feed/",
        },
        {
            "name": "C4ISRNET (Battlefield Tech, AI & EW)",
            "url": "https://www.c4isrnet.com/arc/outboundfeeds/rss/?outputType=xml",
        },
        {
            "name": "Naval News (Global Fleet & Submarines)",
            "url": "https://www.navalnews.com/feed/",
        },
        {
            "name": "Janes Defence & Intelligence Watch",
            "url": "https://news.google.com/rss/search?q=site:janes.com+OR+%22Janes+Defence%22+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "CSIS & IISS Defense & Weapons Analysis",
            "url": "https://news.google.com/rss/search?q=(site:csis.org+OR+site:iiss.org+OR+site:rusi.org)+(military+OR+weapons+OR+missile+OR+drone+OR+defense)+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "DARPA & Pentagon R&D Watch",
            "url": "https://news.google.com/rss/search?q=(DARPA+OR+%22Defense+Innovation+Unit%22+OR+Pentagon)+(%22new+weapon%22+OR+autonomous+OR+hypersonic+OR+drone+OR+AI)+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Military AI & Autonomous Weapons",
            "url": "https://news.google.com/rss/search?q=(%22military+AI%22+OR+%22autonomous+weapons%22+OR+%22defense+tech%22+OR+Anduril+OR+%22Shield+AI%22+OR+Palantir)+when:5d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Drone Warfare, FPV & Counter-UAS Tech",
            "url": "https://news.google.com/rss/search?q=(%22drone+warfare%22+OR+%22loitering+munition%22+OR+%22drone+swarm%22+OR+%22FPV+drone%22+OR+%22counter-UAS%22+OR+%22unmanned+combat%22)+when:4d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Hypersonics, Missiles & Air Defense",
            "url": "https://news.google.com/rss/search?q=(%22hypersonic+missile%22+OR+%22air+defense+system%22+OR+%22Iron+Dome%22+OR+%22Patriot+missile%22+OR+%22ballistic+missile%22+OR+%22laser+weapon%22)+when:4d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Stealth Fighters & Sixth-Gen Combat Aircraft",
            "url": "https://news.google.com/rss/search?q=(%22stealth+fighter%22+OR+F-35+OR+B-21+OR+J-20+OR+NGAD+OR+%22sixth-generation+fighter%22+OR+%22loyal+wingman%22)+when:5d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Electronic Warfare, Cyber & Space Weapons",
            "url": "https://news.google.com/rss/search?q=(%22electronic+warfare%22+OR+%22GPS+jamming%22+OR+%22directed+energy+weapon%22+OR+%22military+satellite%22+OR+%22anti-satellite%22)+when:5d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Submarines, Aircraft Carriers & Sea Drones",
            "url": "https://news.google.com/rss/search?q=(%22nuclear+submarine%22+OR+%22aircraft+carrier%22+OR+%22unmanned+surface+vessel%22+OR+%22naval+weapons%22+OR+%22anti-ship+missile%22)+when:5d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Global Arms & Defense Prime Contractors",
            "url": "https://news.google.com/rss/search?q=(%22Lockheed+Martin%22+OR+Raytheon+OR+%22Northrop+Grumman%22+OR+Rheinmetall+OR+%22BAE+Systems%22+OR+%22weapons+development%22)+when:4d&hl=en-US&gl=US&ceid=US:en",
        },
    ],
    "Technology & Computer Science": [
        {
            "name": "MIT Technology Review",
            "url": "https://www.technologyreview.com/feed/",
        },
        {
            "name": "IEEE Spectrum",
            "url": "https://spectrum.ieee.org/feeds/feed.rss",
        },
        {
            "name": "Communications of the ACM",
            "url": "https://cacm.acm.org/feed/",
        },
        {
            "name": "Hacker News",
            "url": "https://hnrss.org/frontpage",
        },
        {
            "name": "Ars Technica",
            "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        },
        {
            "name": "Wired",
            "url": "https://www.wired.com/feed/rss",
        },
        {
            "name": "The Verge",
            "url": "https://www.theverge.com/rss/index.xml",
        },
        {
            "name": "TechCrunch",
            "url": "https://techcrunch.com/feed/",
        },
        {
            "name": "Financial Times Technology",
            "url": "https://www.ft.com/technology?format=rss",
        },
        {
            "name": "Bloomberg & Reuters Technology",
            "url": "https://news.google.com/rss/search?q=(site:bloomberg.com+OR+site:reuters.com)+technology+OR+semiconductors+when:2d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Semiconductors & Chip Industry (TSMC/ASML)",
            "url": "https://news.google.com/rss/search?q=(TSMC+OR+ASML+OR+NVIDIA+OR+semiconductor+OR+%22chip+manufacturing%22)+when:3d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Krebs on Security (Cybersecurity)",
            "url": "https://krebsonsecurity.com/feed/",
        },
        {
            "name": "The Hacker News (Cybersecurity)",
            "url": "https://feeds.feedburner.com/TheHackersNews",
        },
        {
            "name": "InfoQ (Software Architecture)",
            "url": "https://feed.infoq.com/",
        },
        {
            "name": "Lobsters",
            "url": "https://lobste.rs/rss",
        },
        {
            "name": "DEV Community",
            "url": "https://dev.to/feed",
        },
        {
            "name": "O'Reilly Radar",
            "url": "https://www.oreilly.com/radar/feed/",
        },
        {
            "name": "ZDNet",
            "url": "https://www.zdnet.com/news/rss.xml",
        },
    ],
    "AI": [
        {
            "name": "OpenAI News",
            "url": "https://openai.com/news/rss.xml",
        },
        {
            "name": "Google DeepMind",
            "url": "https://deepmind.google/blog/rss.xml",
        },
        {
            "name": "Anthropic News & Research",
            "url": "https://news.google.com/rss/search?q=site:anthropic.com+OR+Anthropic+Claude+AI+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "MIT News AI",
            "url": "https://news.mit.edu/rss/topic/artificial-intelligence2",
        },
        {
            "name": "Berkeley AI Research (BAIR)",
            "url": "https://bair.berkeley.edu/blog/feed.xml",
        },
        {
            "name": "Stanford HAI & AI Research",
            "url": "https://news.google.com/rss/search?q=site:hai.stanford.edu+OR+%22Stanford+AI%22+when:14d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "arXiv cs.AI (Artificial Intelligence)",
            "url": "https://rss.arxiv.org/rss/cs.AI",
        },
        {
            "name": "arXiv cs.CL (Computation & Language / LLMs)",
            "url": "https://rss.arxiv.org/rss/cs.CL",
        },
        {
            "name": "arXiv cs.LG (Machine Learning)",
            "url": "https://rss.arxiv.org/rss/cs.LG",
        },
        {
            "name": "Hugging Face Blog",
            "url": "https://huggingface.co/blog/feed.xml",
        },
        {
            "name": "NVIDIA Blog",
            "url": "https://blogs.nvidia.com/feed/",
        },
        {
            "name": "Microsoft Research AI",
            "url": "https://www.microsoft.com/en-us/research/feed/",
        },
        {
            "name": "Meta AI & Open Source LLMs",
            "url": "https://news.google.com/rss/search?q=%22Meta+AI%22+OR+Llama+model+AI+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "MIT Technology Review AI",
            "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
        },
        {
            "name": "Financial Times & Reuters AI",
            "url": "https://news.google.com/rss/search?q=(site:ft.com+OR+site:reuters.com)+%22artificial+intelligence%22+when:3d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "VentureBeat AI",
            "url": "https://venturebeat.com/category/ai/feed/",
        },
        {
            "name": "Unite.AI",
            "url": "https://www.unite.ai/feed/",
        },
        {
            "name": "Google News (AI Breakthroughs & Agents)",
            "url": "https://news.google.com/rss/search?q=(%22AI+agents%22+OR+%22large+language+model%22+OR+%22foundation+model%22)+when:2d&hl=en-US&gl=US&ceid=US:en",
        },
    ],
    "Business & Economy": [
        {
            "name": "The Economist (Finance & Economics)",
            "url": "https://www.economist.com/finance-and-economics/rss.xml",
        },
        {
            "name": "The Economist (Business)",
            "url": "https://www.economist.com/business/rss.xml",
        },
        {
            "name": "Financial Times (Global Economy)",
            "url": "https://www.ft.com/global-economy?format=rss",
        },
        {
            "name": "Financial Times (Markets)",
            "url": "https://www.ft.com/markets?format=rss",
        },
        {
            "name": "Bloomberg Markets",
            "url": "https://feeds.bloomberg.com/markets/news.rss",
        },
        {
            "name": "Wall Street Journal (WSJ Markets)",
            "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        },
        {
            "name": "Wall Street Journal (Economy)",
            "url": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
        },
        {
            "name": "Reuters Business & Global Markets",
            "url": "https://news.google.com/rss/search?q=site:reuters.com+(economy+OR+markets+OR+inflation+OR+%22central+bank%22+OR+gold)+when:2d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Nikkei Asia (Business & Economy)",
            "url": "https://news.google.com/rss/search?q=site:asia.nikkei.com+(economy+OR+business+OR+markets+OR+trade)+when:3d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Harvard Business Review (HBR)",
            "url": "http://feeds.hbr.org/harvardbusiness",
        },
        {
            "name": "CNBC World Economy",
            "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        },
        {
            "name": "Fortune Magazine",
            "url": "https://fortune.com/feed/",
        },
        {
            "name": "Forbes Business",
            "url": "https://www.forbes.com/business/feed/",
        },
        {
            "name": "MarketWatch Top Stories",
            "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        },
        {
            "name": "BBC Business",
            "url": "https://feeds.bbci.co.uk/news/business/rss.xml",
        },
        {
            "name": "IMF, World Bank & Federal Reserve Watch",
            "url": "https://news.google.com/rss/search?q=(%22Federal+Reserve%22+OR+IMF+OR+%22World+Bank%22+OR+%22interest+rates%22+OR+%22gold+price%22)+when:2d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "SCMP & CNA Asia Business",
            "url": "https://news.google.com/rss/search?q=(site:scmp.com+OR+site:channelnewsasia.com)+(business+OR+economy+OR+ASEAN+OR+trade)+when:2d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Myanmar Economy, Trade & Opportunities",
            "url": "https://news.google.com/rss/search?q=Myanmar+(economy+OR+business+OR+kyat+OR+trade+OR+banking+OR+gold+OR+investment+OR+opportunity)+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
    ],
    "Science": [
        {
            "name": "Nature",
            "url": "https://www.nature.com/nature.rss",
        },
        {
            "name": "Science Magazine (AAAS)",
            "url": "https://www.science.org/rss/news_current.xml",
        },
        {
            "name": "Quanta Magazine",
            "url": "https://www.quantamagazine.org/feed/",
        },
        {
            "name": "Scientific American",
            "url": "http://rss.sciam.com/ScientificAmerican-Global",
        },
        {
            "name": "New Scientist",
            "url": "https://www.newscientist.com/feed/home/",
        },
        {
            "name": "MIT News (Science & Engineering)",
            "url": "https://news.mit.edu/rss/research",
        },
        {
            "name": "Physics World",
            "url": "https://physicsworld.com/feed/",
        },
        {
            "name": "Phys.org",
            "url": "https://phys.org/rss-feed/",
        },
        {
            "name": "ScienceDaily All",
            "url": "https://www.sciencedaily.com/rss/all.xml",
        },
        {
            "name": "NASA Breaking News",
            "url": "https://www.nasa.gov/news-release/feed/",
        },
        {
            "name": "Space.com",
            "url": "https://www.space.com/feeds/all",
        },
        {
            "name": "Smithsonian Magazine (Science & Nature)",
            "url": "https://www.smithsonianmag.com/rss/science-nature/",
        },
        {
            "name": "The Economist (Science & Technology)",
            "url": "https://www.economist.com/science-and-technology/rss.xml",
        },
        {
            "name": "NYT Science",
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
        },
        {
            "name": "EurekAlert! Science News",
            "url": "https://feeds.eurekalert.org/rss/technology_engineering.xml",
        },
        {
            "name": "Live Science",
            "url": "https://www.livescience.com/feeds/all",
        },
        {
            "name": "BBC Science & Environment",
            "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        },
        {
            "name": "ScienceDirect Research Watch",
            "url": "https://news.google.com/rss/search?q=site:sciencedirect.com+OR+site:cell.com+research&hl=en-US&gl=US&ceid=US:en",
        },
    ],
    "Health & Wellness": [
        {
            "name": "STAT News (Biotech & Medicine)",
            "url": "https://www.statnews.com/feed/",
        },
        {
            "name": "Harvard Health Publishing",
            "url": "https://www.health.harvard.edu/blog/feed",
        },
        {
            "name": "Mayo Clinic News Network",
            "url": "https://newsnetwork.mayoclinic.org/feed/",
        },
        {
            "name": "The Lancet & NEJM Watch",
            "url": "https://news.google.com/rss/search?q=(site:thelancet.com+OR+site:nejm.org+OR+site:jamanetwork.com)+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Nature Medicine & Biotech",
            "url": "https://www.nature.com/nm.rss",
        },
        {
            "name": "World Health Organization (WHO)",
            "url": "https://www.who.int/rss-feeds/news-english.xml",
        },
        {
            "name": "NIH (National Institutes of Health)",
            "url": "https://news.google.com/rss/search?q=site:nih.gov+health+OR+clinical+OR+research+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "NYT Health & Well",
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
        },
        {
            "name": "ScienceDaily Health & Medicine",
            "url": "https://www.sciencedaily.com/rss/health_medicine.xml",
        },
        {
            "name": "Medical News Today",
            "url": "https://www.medicalnewstoday.com/feed",
        },
        {
            "name": "Medical Xpress",
            "url": "https://medicalxpress.com/rss-feed/",
        },
        {
            "name": "BBC Health",
            "url": "https://feeds.bbci.co.uk/news/health/rss.xml",
        },
        {
            "name": "Johns Hopkins & Cleveland Clinic Watch",
            "url": "https://news.google.com/rss/search?q=(%22Johns+Hopkins%22+OR+%22Cleveland+Clinic%22)+health+OR+longevity+OR+medicine+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Healthline",
            "url": "https://www.healthline.com/feed",
        },
        {
            "name": "WebMD Health",
            "url": "https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
        },
        {
            "name": "Psychology Today",
            "url": "https://www.psychologytoday.com/us/front/feed",
        },
        {
            "name": "American Society for Nutrition",
            "url": "https://nutrition.org/feed/",
        },
        {
            "name": "Longevity, Neuroscience & Metabolic Health",
            "url": "https://news.google.com/rss/search?q=(longevity+OR+neuroscience+OR+microbiome+OR+immunotherapy+OR+%22clinical+trial%22)+when:4d&hl=en-US&gl=US&ceid=US:en",
        },
    ],
    "Environment": [
        {
            "name": "Yale Environment 360",
            "url": "https://e360.yale.edu/feed.xml",
        },
        {
            "name": "Carbon Brief",
            "url": "https://www.carbonbrief.org/feed/",
        },
        {
            "name": "Inside Climate News",
            "url": "https://insideclimatenews.org/feed/",
        },
        {
            "name": "Nature Climate Change",
            "url": "https://www.nature.com/nclimate.rss",
        },
        {
            "name": "The Guardian Environment",
            "url": "https://www.theguardian.com/environment/rss",
        },
        {
            "name": "NYT Climate & Environment",
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/Climate.xml",
        },
        {
            "name": "Mongabay",
            "url": "https://news.mongabay.com/feed/",
        },
        {
            "name": "Climate Home News",
            "url": "https://www.climatechangenews.com/feed/",
        },
        {
            "name": "Grist",
            "url": "https://grist.org/feed/",
        },
        {
            "name": "Canary Media (Clean Energy)",
            "url": "https://www.canarymedia.com/rss.rss",
        },
        {
            "name": "CleanTechnica",
            "url": "https://cleantechnica.com/feed/",
        },
        {
            "name": "World Resources Institute (WRI)",
            "url": "https://www.wri.org/rss.xml",
        },
        {
            "name": "ScienceDaily Earth & Climate",
            "url": "https://www.sciencedaily.com/rss/earth_climate.xml",
        },
        {
            "name": "Renewable Energy World",
            "url": "https://www.renewableenergyworld.com/feed/",
        },
        {
            "name": "IUCN News",
            "url": "https://www.iucn.org/rss.xml",
        },
        {
            "name": "Reuters & Bloomberg Energy Transition",
            "url": "https://news.google.com/rss/search?q=(site:reuters.com+OR+site:bloomberg.com)+(%22clean+energy%22+OR+climate+OR+solar+OR+battery+OR+nuclear)+when:3d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "IEA & Global Renewables Watch",
            "url": "https://news.google.com/rss/search?q=(%22International+Energy+Agency%22+OR+UNFCCC+OR+decarbonization+OR+%22grid+storage%22)+when:5d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Earth Times",
            "url": "https://www.earthtimes.org/feed/",
        },
    ],
    "Opinion, Editorial & Feature Stories": [
        {
            "name": "Foreign Affairs (Essays)",
            "url": "https://www.foreignaffairs.com/rss.xml",
        },
        {
            "name": "The Economist (Leaders)",
            "url": "https://www.economist.com/leaders/rss.xml",
        },
        {
            "name": "Financial Times (Opinion)",
            "url": "https://www.ft.com/opinion?format=rss",
        },
        {
            "name": "Project Syndicate",
            "url": "https://www.project-syndicate.org/rss",
        },
        {
            "name": "The Atlantic",
            "url": "https://www.theatlantic.com/feed/all/",
        },
        {
            "name": "The New Yorker",
            "url": "https://www.newyorker.com/feed/everything",
        },
        {
            "name": "New York Times Opinion",
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/Opinion.xml",
        },
        {
            "name": "Wall Street Journal Opinion",
            "url": "https://feeds.a.dj.com/rss/RSSOpinion.xml",
        },
        {
            "name": "Washington Post Opinion",
            "url": "https://feeds.washingtonpost.com/rss/opinions",
        },
        {
            "name": "The Guardian Comment is Free",
            "url": "https://www.theguardian.com/uk/commentisfree/rss",
        },
        {
            "name": "Bloomberg Opinion",
            "url": "https://feeds.bloomberg.com/bview/news.rss",
        },
        {
            "name": "Noema Magazine (Berggruen Institute)",
            "url": "https://www.noemamag.com/feed/",
        },
        {
            "name": "Aeon Magazine",
            "url": "https://aeon.co/feed.rss",
        },
        {
            "name": "Longreads",
            "url": "https://longreads.com/feed/",
        },
        {
            "name": "The Irrawaddy Opinion & Commentary",
            "url": "https://www.irrawaddy.com/category/opinion/feed",
        },
        {
            "name": "Nikkei Asia & SCMP Opinion",
            "url": "https://news.google.com/rss/search?q=(site:asia.nikkei.com+OR+site:scmp.com)+opinion+OR+commentary+when:5d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Brookings & Carnegie Commentary",
            "url": "https://news.google.com/rss/search?q=(site:brookings.edu+OR+site:carnegieendowment.org)+commentary+OR+analysis+when:7d&hl=en-US&gl=US&ceid=US:en",
        },
        {
            "name": "Google News (Geopolitics & Strategy Essays)",
            "url": "https://news.google.com/rss/search?q=(geopolitics+OR+%22military+strategy%22+OR+Myanmar)+opinion+analysis+when:4d&hl=en-US&gl=US&ceid=US:en",
        },
    ],
}
