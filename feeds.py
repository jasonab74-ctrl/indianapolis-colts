# FEEDS for Indianapolis Colts — News

FEEDS = [
    # --- High-signal team feeds
    {"name": "Colts.com",       "url": "https://www.colts.com/news/rss"},
    {"name": "Stampede Blue",   "url": "https://www.stampedeblue.com/rss/index.xml"},
    {"name": "Colts Wire",      "url": "https://coltswire.usatoday.com/feed/"},
    # Some publishers lack stable RSS; Google News backfills & we normalize publisher names
    {"name": "Google News — Colts", "url": "https://news.google.com/rss/search?q=%22Indianapolis+Colts%22+OR+%22Indy+Colts%22&hl=en-US&gl=US&ceid=US:en"},

    # --- Reddit (single clean subreddit; collector will label source as 'Reddit — r/Colts')
    {"name": "Reddit — r/Colts", "url": "https://www.reddit.com/r/Colts/.rss"},

    # Optional extra aggregators (kept to a minimum—Google News already pulls many)
    {"name": "SB Nation (NFL Colts)", "url": "https://www.sbnation.com/rss/index.xml"},
]

# Buttons at the top of the site (labels + URLs)
STATIC_LINKS = [
    {"label": "Schedule",              "url": "https://www.colts.com/schedule/"},
    {"label": "Roster",                "url": "https://www.colts.com/team/players-roster/"},
    {"label": "Depth Chart",           "url": "https://www.espn.com/nfl/team/depth/_/name/ind/indianapolis-colts"},
    {"label": "Injury Report",         "url": "https://www.colts.com/team/injury-report/"},
    {"label": "Fan Zone",              "url": "https://www.colts.com/fans/"},
    {"label": "Team Shop",             "url": "https://shop.colts.com/"},
    {"label": "Tickets",               "url": "https://www.colts.com/tickets/"},
    {"label": "Reddit",                "url": "https://www.reddit.com/r/Colts/"},
    {"label": "Bleacher Report",       "url": "https://bleacherreport.com/indianapolis-colts"},
    {"label": "ESPN Team",             "url": "https://www.espn.com/nfl/team/_/name/ind/indianapolis-colts"},
    {"label": "Yahoo Team",            "url": "https://sports.yahoo.com/nfl/teams/ind/"},
    {"label": "PFF Team Page",         "url": "https://www.pff.com/nfl/teams/indianapolis-colts"},
    {"label": "Pro-Football-Reference","url": "https://www.pro-football-reference.com/teams/clt/"},
    {"label": "NFL Power Rankings",    "url": "https://www.nfl.com/news/power-rankings"},
    {"label": "Stats",                 "url": "https://www.teamrankings.com/nfl/team/indianapolis-colts"},
    {"label": "Standings",             "url": "https://www.nfl.com/standings/league/2025/REG"}
]