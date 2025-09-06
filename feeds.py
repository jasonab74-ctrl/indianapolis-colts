# feeds.py — Indianapolis Colts

TEAM_NAME = "Indianapolis Colts Football"
TEAM_SLUG = "indianapolis-colts"

TEAM_COLORS = {"primary": "#003A70", "secondary": "#FFFFFF", "text": "#111111"}

TEAM_KEYWORDS = [
    "Indianapolis Colts", "Indy Colts", "Colts",
    "Lucas Oil Stadium", "Shane Steichen",
    "Anthony Richardson", "Michael Pittman", "Michael Pittman Jr",
    "Jonathan Taylor", "DeForest Buckner", "Quenton Nelson", "Kenny Moore",
]

SPORT_TOKENS = ["NFL", "football", "National Football League", "Colts"]

# Tight exclusions only (do NOT exclude opponents)
EXCLUDE_TOKENS = [
    "Pacers", "basketball", "baseball", "softball", "soccer", "volleyball", "hockey",
    "Notre Dame", "Fighting Irish", "Hoosiers", "Boilermakers", "Purdue", "Indiana University",
    "House of Houston",
]

# Trusted outlets bypass strict filters
FEEDS = [
    {"name": "colts.com", "url": "https://www.colts.com/rss", "trusted": True},
    {"name": "NFL.com — Indianapolis Colts", "url": "https://www.nfl.com/rss/team/ind", "trusted": True},
    {"name": "Colts Wire (USA Today)", "url": "https://coltswire.usatoday.com/feed/", "trusted": True},
    {"name": "Stampede Blue", "url": "https://www.stampedeblue.com/rss/index.xml", "trusted": True},
    {"name": "ESPN — Indianapolis Colts", "url": "https://www.espn.com/blog/indianapolis-colts/rss", "trusted": True},
    {"name": "NBC Sports — Colts", "url": "https://www.nbcsports.com/rss/team/indianapolis-colts", "trusted": True},
    {"name": "Bleacher Report — Colts", "url": "https://bleacherreport.com/articles/feed?tag_id=2604", "trusted": True},
    {"name": "Yahoo Sports — Colts", "url": "https://sports.yahoo.com/nfl/teams/ind/rss/", "trusted": True},
    {"name": "Reddit — r/Colts", "url": "https://www.reddit.com/r/Colts/.rss", "trusted": True},
    {"name": "Sports Illustrated — Horseshoe Huddle", "url": "https://www.si.com/nfl/colts/.rss", "trusted": True},
    {"name": "ProFootballTalk — Colts", "url": "https://profootballtalk.nbcsports.com/team/indianapolis-colts/feed/", "trusted": True},

    # Aggregators (filtered)
    {"name": "\"Indianapolis Colts\" — Google News",
     "url": "https://news.google.com/rss/search?q=%22Indianapolis+Colts%22&hl=en-US&gl=US&ceid=US:en",
     "trusted": False},
    {"name": "Bing News — Indianapolis Colts",
     "url": "https://www.bing.com/news/search?q=Indianapolis+Colts&format=rss",
     "trusted": False},
]

# Buttons row (Rams-style: many good shortcuts)
STATIC_LINKS = [
    {"label": "Schedule", "url": "https://www.colts.com/schedule/"},
    {"label": "Roster", "url": "https://www.colts.com/team/players-roster/"},
    {"label": "Depth Chart", "url": "https://www.ourlads.com/nfldepthcharts/depthchart/IND"},
    {"label": "Injury Report", "url": "https://www.colts.com/team/injury-report/"},
    {"label": "Fan Zone", "url": "https://www.colts.com/fans"},
    {"label": "Team Shop", "url": "https://shop.colts.com/"},
    {"label": "Tickets", "url": "https://www.ticketmaster.com/indianapolis-colts-tickets/artist/805935"},

    {"label": "Reddit", "url": "https://www.reddit.com/r/Colts/"},
    {"label": "Bleacher Report", "url": "https://bleacherreport.com/indianapolis-colts"},
    {"label": "ESPN Team", "url": "https://www.espn.com/nfl/team/_/name/ind/indianapolis-colts"},
    {"label": "Yahoo Team", "url": "https://sports.yahoo.com/nfl/teams/ind/"},
    {"label": "PFF Team Page", "url": "https://www.pff.com/nfl/teams/indianapolis-colts"},
    {"label": "Pro-Football-Reference", "url": "https://www.pro-football-reference.com/teams/clt/"},
    {"label": "NFL Power Rankings", "url": "https://www.nfl.com/news/power-rankings"},
    {"label": "Stats", "url": "https://www.espn.com/nfl/team/stats/_/name/ind/indianapolis-colts"},
    {"label": "Standings", "url": "https://www.nfl.com/standings/league/2025/REG"},
]