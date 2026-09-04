import os
from dotenv import load_dotenv

# Load .env from project root (repo root, 2 levels up from this file)
_project_root = os.path.join(os.path.dirname(__file__), "..", "..")
load_dotenv(os.path.join(_project_root, ".env"))

# Project settings and configuration variables

# Storage mode: "mongodb" or "local"
# When set to "local", scraped articles are saved to LOCAL_PENDING_DIR
# and WikiIngestAgent reads from that directory instead of MongoDB.
USE_LOCAL_STORAGE = os.environ.get("USE_LOCAL_STORAGE", "false").lower() == "true"
LOCAL_PENDING_DIR = os.environ.get("LOCAL_PENDING_DIR", os.path.join(_project_root, "pending_articles"))

# Storage mode: "mongodb" or "local"
# When set to "local", scraped articles are saved to LOCAL_PENDING_DIR
# and WikiIngestAgent reads from that directory instead of MongoDB.
USE_LOCAL_STORAGE = os.environ.get("USE_LOCAL_STORAGE", "false").lower() == "true"
LOCAL_PENDING_DIR = os.environ.get("LOCAL_PENDING_DIR", os.path.join(_project_root, "pending_articles"))

# Database connection strings/configs
RAW_DATA_DB_CONFIG = {
    "type": "mongodb",
    "host": os.environ.get("MONGO_HOST", "192.168.3.8"),
    "port": int(os.environ.get("MONGO_PORT", "49157")),
    "db_name": os.environ.get("MONGO_DB_NAME", "content_operation"),
    "collection_name": os.environ.get("MONGO_COLLECTION", "rss_raw_content"),
}

KNOWLEDGE_BASE_DB_CONFIG = {
    "type": "postgresql",
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", "5432")),
    "db_name": os.environ.get("PG_DB_NAME", "content_knowledge_base"),
    "user": os.environ.get("PG_USER", "user"),
    "password": os.environ.get("PG_PASSWORD", ""),
}
AI_HIGH_SCORE = [
  "https://www.bestblogs.dev/en/feeds/rss?category=ai&minScore=90",
  "https://www.bestblogs.dev/feeds/rss?featured=y"
]
CODING_PATTERN = [
  "https://www.bestblogs.dev/feeds/rss?category=programming&type=article"
]
INFO_RESOURCES = [
  "https://simonwillison.net/atom/everything/",
  "https://www.jeffgeerling.com/blog.xml",
  "https://www.seangoedecke.com/rss.xml",
  "https://krebsonsecurity.com/feed/",
  "https://daringfireball.net/feeds/main",
  "https://ericmigi.com/rss.xml",
  "http://antirez.com/rss",
  "https://idiallo.com/feed.rss",
  "https://maurycyz.com/index.xml",
  "https://pluralistic.net/feed/",
  "https://shkspr.mobi/blog/feed/",
  "https://lcamtuf.substack.com/feed",
  "https://mitchellh.com/feed.xml",
  "https://dynomight.net/feed.xml",
  "https://utcc.utoronto.ca/~cks/space/blog/?atom",
  "https://xeiaso.net/blog.rss",
  "https://devblogs.microsoft.com/oldnewthing/feed",
  "https://www.righto.com/feeds/posts/default",
  "https://lucumr.pocoo.org/feed.atom",
  "https://garymarcus.substack.com/feed",
  "https://rachelbythebay.com/w/atom.xml",
  "https://overreacted.io/rss.xml",
  "https://timsh.org/rss/",
  "https://www.johndcook.com/blog/feed/",
  "https://gilesthomas.com/feed/rss.xml",
  "https://matklad.github.io/feed.xml",
  "https://www.theatlantic.com/feed/author/derek-thompson/",
  "https://evanhahn.com/feed.xml",
  "https://terriblesoftware.org/feed/",
  "https://rakhim.exotext.com/rss.xml",
  "https://joanwestenberg.com/rss",
  "https://xania.org/feed",
  "https://micahflee.com/feed/",
  "https://nesbitt.io/feed.xml",
  "https://feed.tedium.co/",
  "https://susam.net/feed.xml",
  "https://entropicthoughts.com/feed.xml",
  "https://buttondown.com/hillelwayne/rss",
  "https://www.dwarkeshpatel.com/feed",
  "https://borretti.me/feed.xml",
  "https://www.wheresyoured.at/rss/",
  "https://jayd.ml/feed.xml",
  "https://minimaxir.com/index.xml",
  "https://geohot.github.io/blog/feed.xml",
  "http://www.aaronsw.com/2002/feeds/pgessays.rss",
  "https://www.filfre.net/feed/",
  "https://blog.jim-nielsen.com/feed.xml",
  "https://dfarq.homeip.net/feed/",
  "https://jyn.dev/atom.xml",
  "https://www.geoffreylitt.com/feed.xml",
  "https://www.downtowndougbrown.com/feed/",
  "https://brutecat.com/rss.xml",
  "https://eli.thegreenplace.net/feeds/all.atom.xml",
  "https://www.abortretry.fail/feed",
  "https://fabiensanglard.net/rss.xml",
  "https://oldvcr.blogspot.com/feeds/posts/default",
  "https://bogdanthegeek.github.io/blog/index.xml",
  "https://hugotunius.se/feed.xml",
  "https://gwern.substack.com/feed",
  "https://berthub.eu/articles/index.xml",
  "https://chadnauseam.com/rss.xml",
  "https://simone.org/feed/",
  "https://it-notes.dragas.net/feed/",
  "https://beej.us/blog/rss.xml",
  "https://hey.paris/index.xml",
  "https://danielwirtz.com/rss.xml",
  "https://matduggan.com/rss/",
  "https://refactoringenglish.com/index.xml",
  "https://worksonmymachine.substack.com/feed",
  "https://philiplaine.com/index.xml",
  "https://steveblank.com/feed/",
  "https://bernsteinbear.com/feed.xml",
  "https://danieldelaney.net/feed",
  "https://www.troyhunt.com/rss/",
  "https://herman.bearblog.dev/feed/",
  "https://tomrenner.com/index.xml",
  "https://martinalderson.com/feed.xml",
  "https://danielchasehooper.com/feed.xml",
  "https://www.chiark.greenend.org.uk/~sgtatham/quasiblog/feed.xml",
  "https://grantslatton.com/rss.xml",
  "https://www.experimental-history.com/feed",
  "https://anildash.com/feed.xml",
  "https://aresluna.org/main.rss",
  "https://michael.stapelberg.ch/feed.xml",
  "https://blog.miguelgrinberg.com/feed",
  "https://keygen.sh/blog/feed.xml",
  "https://mjg59.dreamwidth.org/data/rss",
  "https://computer.rip/rss.xml",
  # Twitter/X RSS via xgo.ing
  "https://api.xgo.ing/rss/user/0c0856a69f9f49cf961018c32a0b0049",  # OpenAI
  "https://api.xgo.ing/rss/user/971dc1fc90da449bac23e5fad8a33d55",  # OpenAI Developers
  "https://api.xgo.ing/rss/user/f7992687b8d74b14bf2341eb3a0a5ec4",  # ChatGPT
  "https://api.xgo.ing/rss/user/e30d4cd223f44bed9d404807105c8927",  # Sam Altman
  "https://api.xgo.ing/rss/user/fc28a211471b496682feff329ec616e5",  # Anthropic
  "https://api.xgo.ing/rss/user/49666ce6fe3e4cb786c6574684542ec5",  # Dario Amodei
  "https://api.xgo.ing/rss/user/524525de0d69407b80f0a7d891fdc8df",  # Alex Albert
  "https://api.xgo.ing/rss/user/af19d054e26a49129f23abfa82d9e268",  # Greg Brockman
  "https://api.xgo.ing/rss/user/78d7b99318b04b309b04000f7e24da29",  # Mike Krieger
  "https://api.xgo.ing/rss/user/3ca3c7698fd04611a0e7d14fae93c84c",  # Kevin Weil
  "https://api.xgo.ing/rss/user/63316630d94543f5a6480f230f483008",  # Marc Andreessen
  "https://api.xgo.ing/rss/user/61f4b78554fb4b8fa5653ec5d924d15a",  # Microsoft Research
  "https://api.xgo.ing/rss/user/edf707b5c0b248579085f66d7a3c5524",  # Andrej Karpathy
  "https://api.xgo.ing/rss/user/4de0bd2d5cef4333a0260dc8157054a7",  # Google AI
  "https://api.xgo.ing/rss/user/f5f4f928dede472ea55053672ad27ab6",  # Yann LeCun
  "https://api.xgo.ing/rss/user/5f13b32b124a41cfb659f903a84032b1",  # Anton Osika
  "https://api.xgo.ing/rss/user/639cd13d44284e10ac89fbd1c5399767",  # Lovable
  "https://api.xgo.ing/rss/user/a4bfe44bfc0d4c949da21ebd3f5f42a5",  # Fei-Fei Li
  "https://api.xgo.ing/rss/user/5fb1814c610c4af2911caa98c5c5ef82",  # Amjad Masad
  "https://api.xgo.ing/rss/user/613f859e4bc440c5a28f40732840f5cf",  # Replit
  "https://api.xgo.ing/rss/user/5dbd038a8f5140938d0877511571797b",  # clem (HuggingFace)
  "https://api.xgo.ing/rss/user/fc16750ce50741f1b1f05ea1fb29436f",  # Hugging Face
  "https://api.xgo.ing/rss/user/08b5488b20bc437c8bfc317a52e5c26d",  # Andrew Ng
  "https://api.xgo.ing/rss/user/42e6b4901b97498eab2ab64c07d56177",  # DeepLearning.AI
  "https://api.xgo.ing/rss/user/4918efb13c47459b8dcaa79cfdf72d09",  # Thomas Wolf
  "https://api.xgo.ing/rss/user/4f63d960de644aeebd0aa97e4994dafe",  # Logan Kilpatrick
  "https://api.xgo.ing/rss/user/adf65931519340f795e2336910b4cd15",  # Lex Fridman
  "https://api.xgo.ing/rss/user/a636de3cbda0495daabd15b9fd298614",  # Rowan Cheung
  "https://api.xgo.ing/rss/user/ca2fa444b6ea4b8b974fe148056e497a",  # 李继刚
  "https://api.xgo.ing/rss/user/4a884d5e2f3740c5a26c9c093de6388a",  # Demis Hassabis
  "https://api.xgo.ing/rss/user/760ab7cd9708452c9ce1f9144b92a430",  # bolt.new
  "https://api.xgo.ing/rss/user/394acfaff8c44e09936f5bc0b8504f2c",  # Mustafa Suleyman
  "https://api.xgo.ing/rss/user/fafa6df3c67644b1a367a177240e0173",  # Sualeh Asif
  "https://api.xgo.ing/rss/user/082097117b4543e9a741cd2580f936d3",  # Junyang Lin
  "https://api.xgo.ing/rss/user/80032d016d654eb4afe741ff34b7643d",  # Qwen
  "https://api.xgo.ing/rss/user/f54b2b40185943ce8f48a880110b7bc2",  # Binyuan Hui
  "https://api.xgo.ing/rss/user/a99538443a484fcc846bdcc8f50745ec",  # Google DeepMind
  "https://api.xgo.ing/rss/user/05f1492e43514dc3862a076d3697c390",  # NVIDIA AI
  "https://api.xgo.ing/rss/user/57831559d22440debbfb2f2528e4ba84",  # Ian Goodfellow
  "https://api.xgo.ing/rss/user/771b32075fe54a83bdb6966de9647b4f",  # Groq Inc
  "https://api.xgo.ing/rss/user/6bbf31cac345443585c3280320ba9009",  # Berkeley AI Research
  "https://api.xgo.ing/rss/user/b1013166769c49f8aa3fbdc222867054",  # Jeff Dean
  "https://api.xgo.ing/rss/user/c61046471f174d86bc0eb76cb44a21c3",  # Justine Moore
  "https://api.xgo.ing/rss/user/5fca8ccd87344d388bc863304ed6fd86",  # Scott Wu
  "https://api.xgo.ing/rss/user/4cc14cbd15c74e189d537c415369e1a7",  # Cognition
  "https://api.xgo.ing/rss/user/2f1035ec6b28475987af06b600e1d04c",  # Weaviate
  "https://api.xgo.ing/rss/user/e6bb4f612dd24db5bc1a6811e6dd5820",  # Runway
  "https://api.xgo.ing/rss/user/ef7c70f9568d45f4915169fef4ce90b4",  # AI at Meta
  "https://api.xgo.ing/rss/user/d5fc365556e641cba2278f501e8c6f92",  # Stanford AI Lab
  "https://api.xgo.ing/rss/user/cb6169815e2e447e8e6148a4af3f9686",  # Geoffrey Hinton
  "https://api.xgo.ing/rss/user/c65c68f3713747bba863f92d6b5e996f",  # Patrick Loeber
  "https://api.xgo.ing/rss/user/ce352bbf72e44033985bc756db2ee0e2",  # Philipp Schmid
  "https://api.xgo.ing/rss/user/424e67b19eed4500b7a440976bbd2ade",  # Milvus
  "https://api.xgo.ing/rss/user/f510f6e7eecf456ca7e2895a46752888",  # Jina AI
  "https://api.xgo.ing/rss/user/58894bf2934a426ca833c682da2bc810",  # Justin Welsh
  "https://api.xgo.ing/rss/user/72dd496bfd9d44c5a5761a974630376d",  # Midjourney
  "https://api.xgo.ing/rss/user/462aa134ed914f98b3491680ad9b36ed",  # cohere
  "https://api.xgo.ing/rss/user/a55f6e33dd224235aabaabaaf9d58a06",  # Qdrant
  "https://api.xgo.ing/rss/user/7d19a619a1cc4a9896129211269d2c85",  # AI Engineer
  "https://api.xgo.ing/rss/user/a7be8b61a1264ea7984abfaea3eff686",  # Latent.Space
  "https://api.xgo.ing/rss/user/3877c31cdb554cffb750b3b683c98c4d",  # Character.AI
  "https://api.xgo.ing/rss/user/1897eed387064dfab443764d6da50bc6",  # ElevenLabs
  "https://api.xgo.ing/rss/user/2de92402f4a24c90bb27e7580b93a878",  # Taranjeet
  "https://api.xgo.ing/rss/user/94bb691baeff461686326af619beb116",  # mem0
  "https://api.xgo.ing/rss/user/a9aff6b016c143ed8728dd86eb70d7db",  # HeyGen
  "https://api.xgo.ing/rss/user/b9912ac9a29042cf8c834419dc44cb1f",  # Paul Couvert
  "https://api.xgo.ing/rss/user/862fee50a745423c87e2633b274caf1d",  # LangChain
  "https://api.xgo.ing/rss/user/f299207df53745bca04a03db8d11c5aa",  # Harrison Chase
  "https://api.xgo.ing/rss/user/acc648327c614d9b985b9fc3d737165b",  # Recraft
  "https://api.xgo.ing/rss/user/fdd601ea751949e7bec9e4cdad7c8e6c",  # Perplexity
  "https://api.xgo.ing/rss/user/59e6b63ae9684d11be0ae13d9e7420f2",  # Aravind Srinivas
  "https://api.xgo.ing/rss/user/67e259bd5be544ce84bbc867eace54c2",  # LlamaIndex
  "https://api.xgo.ing/rss/user/b3d904c0d7c446558ef3a1e7f2eb362b",  # Jerry Liu
  "https://api.xgo.ing/rss/user/0be252fedbe84ad7bea21be44b18da89",  # Dify
  "https://api.xgo.ing/rss/user/44d9fa384087448a94d3c8595f8d535e",  # Julien Chaumond
  "https://api.xgo.ing/rss/user/6326c63a2dfa445bbde88bea0c3112c2",  # ollama
  "https://api.xgo.ing/rss/user/be74da51698d4cefb12b39830d6cd201",  # FlowiseAI
  "https://api.xgo.ing/rss/user/3306d8b253ec4e03aca3c2e9967e7119",  # Pika
  "https://api.xgo.ing/rss/user/3953aa71e87a422eb9d7bf6ff1c7c43e",  # xAI
  "https://api.xgo.ing/rss/user/a719880fe66e4156a111187f50dae91b",  # Ideogram
  "https://api.xgo.ing/rss/user/8d2d03aea8af49818096da4ea00409d1",  # Mistral AI
  "https://api.xgo.ing/rss/user/e503a90c035c4b1d8f8dd34907d15bf4",  # OpenRouter
  "https://api.xgo.ing/rss/user/dbf37973e6fc4eae91d4be9669a78fc7",  # v0
  "https://api.xgo.ing/rss/user/22af005b21ec45b1a4503acca777b7f0",  # AI SDK
  "https://api.xgo.ing/rss/user/4900b3dcd592424687582ff9e0f148ea",  # Fish Audio
  "https://api.xgo.ing/rss/user/e65b5e59fcb544918c1ba17f5758f0f8",  # Hailuo AI (MiniMax)
  "https://api.xgo.ing/rss/user/4a8273800ed34a069eecdb6c5c1b9ccf",  # Windsurf
  "https://api.xgo.ing/rss/user/7794c4268a504019a94af1778857a703",  # Varun Mohan
  "https://api.xgo.ing/rss/user/97f1484ae48c430fbbf3438099743674",  # 宝玉
  "https://api.xgo.ing/rss/user/320181c4651a41a08015946b55f704ab",  # ManusAI
  "https://api.xgo.ing/rss/user/341f7b9f8d9b477e8bb200caa7f32c6e",  # AK
  "https://api.xgo.ing/rss/user/db648e4d4eae4822aa0d34f0faef7ad2",  # LovartAI
  "https://api.xgo.ing/rss/user/f8a106a09a7d404fb8de7eb0c5ddd2a2",  # Figma
  "https://api.xgo.ing/rss/user/5287b4e0e13a4ab7ab7b1d56f9d88960",  # Cursor
  "https://api.xgo.ing/rss/user/a02496979a0e4d86baf2b72c24db52a4",  # Aman Sanger
  "https://api.xgo.ing/rss/user/65f321be670b4ffba7f40d0afd38c94d",  # eric zakariasson
  "https://api.xgo.ing/rss/user/baa68dbd9a9e461a96fd9b2e3f35dcbf",  # Satya Nadella
  "https://api.xgo.ing/rss/user/71ffd342cb5d478185ef7d55bdfca011",  # Genspark
  "https://api.xgo.ing/rss/user/0277b0bbefd54df7bc6b7880122da8f7",  # orange.ai
  "https://api.xgo.ing/rss/user/244eb9fa77ce4fa3b7fa5ceba80027a4",  # Barsee
  "https://api.xgo.ing/rss/user/6e8e7b42cb434818810f87bcf77d86fb",  # Hunyuan
  "https://api.xgo.ing/rss/user/221a88341acb475db221a12fed8208d0",  # NotebookLM
  "https://api.xgo.ing/rss/user/69d925d4a8d44221b03eecbe07bd0f74",  # Google AI Developers
  "https://api.xgo.ing/rss/user/8324d65a63dc42c584a8c08cc8323c9f",  # Sundar Pichai
  "https://api.xgo.ing/rss/user/6fb337feeec44ca38b79491b971d868d",  # Google Gemini App
  "https://api.xgo.ing/rss/user/ddfdcdd4e390495c942f0b5da62af0fb",  # Eric Jing
  "https://api.xgo.ing/rss/user/77d5ce4736854b0ebae603e4b54d3095",  # Lenny Rachitsky
  "https://api.xgo.ing/rss/user/c6cfe7c0d6b74849997073233fdea840",  # Jim Fan
  "https://api.xgo.ing/rss/user/f97a26863aec4425b021720d4f8e4ede",  # Notion
  "https://api.xgo.ing/rss/user/3434c0d56ee0446f991fb6af42bfac4b",  # Akshay Kothari
  "https://api.xgo.ing/rss/user/0e3ebaf288014c45b0d24b71fe37312b",  # AI Breakfast
  "https://api.xgo.ing/rss/user/68b610deb24b47ae9a236811563cda86",  # DeepSeek
  "https://api.xgo.ing/rss/user/831fac36aa0a49a9af79f35dc1c9b5d9",  # 歸藏(guizang.ai)
  "https://api.xgo.ing/rss/user/6384ee3c656c48fea5e8b3cdacece4d0",  # Dia
  "https://api.xgo.ing/rss/user/6d7d398dd80b48d79669c92745d32cf6",  # Skywork
  "https://api.xgo.ing/rss/user/b43bc203409e4c5a9c3ae86fe1ac00c9",  # Naval
  "https://api.xgo.ing/rss/user/179bcc4b8e5d4274b6e9e935f9fd4434",  # Aadit Sheth
  "https://api.xgo.ing/rss/user/74e542992cf7441390c708f5601071d4",  # 小互
  "https://api.xgo.ing/rss/user/66a6b39ddcfa42e39621e0ab293c1bdd",  # cat
  "https://api.xgo.ing/rss/user/e153fdd077df458b8298d975c060dcc3",  # Augment Code
  "https://api.xgo.ing/rss/user/9de19c78f7454ad08c956c1a00d237fe",  # 向阳乔木
  "https://api.xgo.ing/rss/user/326763c2f6154826babcfd71c5ab0f70",  # Fellou
  "https://api.xgo.ing/rss/user/564237c3de274d58a04f064920817888",  # Kling AI
  "https://api.xgo.ing/rss/user/c04abb206bbf4f91b22795024d6c0614",  # Firecrawl
  "https://api.xgo.ing/rss/user/17687b1051204b2dbaed4ea4c9178f28",  # Poe
  "https://api.xgo.ing/rss/user/f01b088d5a39473e854b07143df77ec5",  # lmarena.ai
  "https://api.xgo.ing/rss/user/12eba9c3db4940c5ab2a72bd00f9ff2c",  # Replicate
  "https://api.xgo.ing/rss/user/f3fedf817599470dbf8d8d11f0872475",  # a16z
  "https://api.xgo.ing/rss/user/b1ab109f6afd42ab8ea32e17a19a3a3e",  # Y Combinator
  "https://api.xgo.ing/rss/user/a8f7e2238039461cbc8bf55f5f194498",  # Lilian Weng
  "https://api.xgo.ing/rss/user/900549ddadf04e839d3f7a17ebaba3fc",  # Paul Graham
  "https://api.xgo.ing/rss/user/e8750659b8154dbfa0489f451e044af1",  # Guillermo Rauch
  "https://api.xgo.ing/rss/user/a3eb6beb2d894da3a9b7ab6d2e46790e",  # andrew chen
  "https://api.xgo.ing/rss/user/d8121d969fb34c7daad2dd2aac4ba270",  # Arthur Mensch
  "https://api.xgo.ing/rss/user/30ad80be93c84e44acc37d5ddf31db57",  # Simon Willison
  "https://api.xgo.ing/rss/user/b8d7530f0b294405825013bbc1cc198f",  # Browser Use
  "https://api.xgo.ing/rss/user/aa74321087f9405a872fd9a76b743bf8",  # AI Will
  "https://api.xgo.ing/rss/user/4838204097ed422eac24ad48e68dc3ff",  # Ray Dalio
  "https://api.xgo.ing/rss/user/baad3713defe4182844d2756b4c2c9ed",  # Sahil Lavingia
  "https://api.xgo.ing/rss/user/931d6e88e067496cac6bf23f69d60f33",  # elvis
  "https://api.xgo.ing/rss/user/83b1ea38940b4a1d81ea57d1ffb12ad7",  # The Rundown AI
  "https://api.xgo.ing/rss/user/6ebdf0d91eef4c149acd0ef110635866",  # Nick St. Pierre
  "https://api.xgo.ing/rss/user/5d749cc613ec4069bb2a47334739e1b6",  # Monica_IM
  "https://api.xgo.ing/rss/user/9f35c76341554bd78c2b9e63dc4fa5d8",  # Fireworks AI
  "https://api.xgo.ing/rss/user/48aae530e0bf413aa7d44380f418e2e3",  # meng shao
  "https://api.xgo.ing/rss/user/dceb5cd131b34c72a8376cba8ea5d864",  # Jan Leike
  "https://api.xgo.ing/rss/user/4d2d4165a7524217a08d3f57f27fa190",  # Richard Socher
  "https://api.xgo.ing/rss/user/35a38c5646d946fb894d8c30c1d9629e",  # Gary Marcus
  "https://api.xgo.ing/rss/user/3042b6f912b24f64982cc23f7bd59681",  # Adam D'Angelo
  "https://api.xgo.ing/rss/user/c961547e08df4396b3ab69367a07a1cd",  # Suhail
  "https://api.xgo.ing/rss/user/5b632b7fba274f62928cdcc9d3db4c5e",  # AI产品黄叔
  "https://api.xgo.ing/rss/user/fa5b15f68a2e4df1ab301e26a4ab9190",  # GitHub
  "https://api.xgo.ing/rss/user/3d72acd51d21414ea39871fc01982a65",  # idoubi
  "https://api.xgo.ing/rss/user/01f60d63a61b44d692cc35c7feb0b4a4",  # Claude
  "https://api.xgo.ing/rss/user/55d2d3f3eaaf4357b3230e0b01a464d7",  # Martin Fowler
  "https://api.xgo.ing/rss/user/aab44cb2665a49258cd81f63b0b55192",  # Viking
  "https://api.xgo.ing/rss/user/9cb3b60e689e4445a7fbdfd0be144126",  # Geek
  "https://api.xgo.ing/rss/user/665fc88440fd4436acbc2e630d824926",  # Tw93
  "https://api.xgo.ing/rss/user/66c40de71a9842fda4853b7d9d1d20da",  # Yangyi
  "https://api.xgo.ing/rss/user/23d41992b29340788aa3d09d8364c5f5"  # hidecloud
]

AI_LAB_RESOURCES = INFO_RESOURCES

# Other settings (API keys, channel info, etc.)

LLM_CONFIG = {
    "azure": {
        "api_url": os.environ.get("AZURE_OPENAI_BASE_URL", ""),
        "api_key": os.environ.get("AZURE_OPENAI_API_KEY", ""),
        "model": os.environ.get("AZURE_OPENAI_MODEL", ""),
    },
    "deepseek": {
        "api_url": os.environ.get("LLM_DEEPSEEK_URL", ""),
        "api_key": os.environ.get("LLM_API_KEY", ""),
        "model": os.environ.get("LLM_DEEPSEEK_MODEL", ""),
    },
    "gpt4o": {
        "api_url": os.environ.get("LLM_GPT4O_URL", ""),
        "api_key": os.environ.get("LLM_API_KEY", ""),
        "model": os.environ.get("LLM_GPT4O_MODEL", ""),
    },
    "glm": {
        "api_url": os.environ.get("ANTHROPIC_BASE_URL", ""),
        "api_key": os.environ.get("ANTHROPIC_AUTH_TOKEN", os.environ.get("ANTHROPIC_API_KEY", "")),
        "model": os.environ.get("ANTHROPIC_MODEL", ""),
    },
}

WECHAT_CONFIG = {
    "appid": os.environ.get("WECHAT_APPID", ""),
    "secret": os.environ.get("WECHAT_SECRET", ""),
    "thumb_media_id": os.environ.get("WECHAT_THUMB_MEDIA_ID", ""),
    "template_id": os.environ.get("WECHAT_TEMPLATE_ID", ""),
}

ECM_CONFIG = {
    "api_url": os.environ.get("ECM_API_URL", "https://rdfa-gateway.ennew.com/ecm/open/message/send"),
    "access_key": os.environ.get("ECM_ACCESS_KEY", ""),
}

GITHUB_CONFIG = {
  "repo_path": os.environ.get("GITHUB_REPO_PATH"),
  "target_dir": "src/app/[locale]/blog/posts",
  "github_token": os.environ.get("GITHUB_TOKEN", ""),
  "repo_url": os.environ.get("GITHUB_REPO_URL", ""),
  "trending_since": os.environ.get("GITHUB_TRENDING_SINCE", "daily"),
  "trending_language": os.environ.get("GITHUB_TRENDING_LANGUAGE", ""),
  "trending_limit": int(os.environ.get("GITHUB_TRENDING_LIMIT", "20")),
}


def build_llm(name: str = None):
    """Build a configured CustomChatModel with an actionable error if config is missing."""
    if name is None:
        if os.environ.get("AZURE_OPENAI_BASE_URL"):
            name = "azure"
        elif os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            name = "glm"
        elif all(os.environ.get(key) for key in ("LLM_GPT4O_URL", "LLM_API_KEY", "LLM_GPT4O_MODEL")):
            name = "gpt4o"
        elif all(os.environ.get(key) for key in ("LLM_DEEPSEEK_URL", "LLM_API_KEY", "LLM_DEEPSEEK_MODEL")):
            name = "deepseek"
        else:
            raise RuntimeError(
                "No LLM is configured. Create a .env file and configure one backend: "
                "AZURE_OPENAI_BASE_URL/AZURE_OPENAI_API_KEY/AZURE_OPENAI_MODEL, "
                "ANTHROPIC_BASE_URL/ANTHROPIC_AUTH_TOKEN/ANTHROPIC_MODEL, or "
                "LLM_GPT4O_URL/LLM_API_KEY/LLM_GPT4O_MODEL."
            )
    from ..agents.custom_llm import CustomChatModel
    if name not in LLM_CONFIG:
        raise ValueError(f"Unknown LLM backend: {name}. Choose from: {', '.join(LLM_CONFIG)}")
    cfg = LLM_CONFIG[name]
    missing = [key for key in ("api_url", "api_key", "model") if not cfg.get(key)]
    if missing:
        raise RuntimeError(f"LLM backend '{name}' is missing configuration: {', '.join(missing)}")
    return CustomChatModel(
        api_url=cfg["api_url"],
        api_key=cfg["api_key"],
        model=cfg["model"],
    )
