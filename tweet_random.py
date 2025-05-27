import random
import time
from tweet import TwitterBot  # Or keep full code here

# 25% chance to tweet
if random.random() < 0.25:
    delay = random.randint(0, 600)  # Random delay: 0–10 minutes
    time.sleep(delay)
    TwitterBot().run()
else:
    print("Skipping this run (random chance).")
