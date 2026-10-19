# 🧪 RAG Pipeline Evaluation Report

**Target API:** `https://3sej72jreh.execute-api.eu-central-1.amazonaws.com/poc/query`  
**Timestamp:** `2026-10-19 14:04:18`

---

### Test `Q-01`: RATINGS

* **Query:** "why do guests leave low star ratings at eastside?"
* **Result:** 🟢 **PASSED**
* **Latency:** `1.23s` | **Status Code:** `200`  
* **Matched Keywords:** `['eastside', 'food', 'service', 'star']`

**Generated Answer:**
> Guests leave low star ratings at eastside primarily due to poor food quality and notably slow service. Many reviews highlight subpar dishes and disappointing experiences with the staff.

<details>
<summary><b>View Retrieved Context (4 chunks)</b></summary>

1. **[ID: BCLvpd08Ci4Tcq-fIRhZdA | eastside | Rating: 2.0]**: Leaving this 2-star review in response to the food, not the place as a drinking/hangout spot...although the wine was crap, too. 2-Stars awarded for the Nintendo 64 and all of the nostalgia-worthy games, the decent choice of drafts (even if they were out of the draft I ordered), and the great service from the staff. The food, on the other hand, will make you wish you had eaten at home. My wife and I went out as a treat because we didn't feel like cooking, but the majority of our food was sub-par. I got the shrimp po-boy which was not a po-boy by definition (it was just shrimp on a crappy sandwich...no French bread, no Cajun sauce or even enough Cajun seasoning, and the shrimp was obviously frozen-thawed not fresh). One of the shrimps was even gray when I bit into it, and the sandwich itself smelled more like old fish than fresh shrimp. My wife got the Athena chicken sandwich and that was just so-so, with the overwhelming taste of feta disguising the low-quality factory chicken they use for the sandwich. The best part of our collective meals was the mixed greens we ordered as a side, so I wouldn't exactly recommend ordering food here unless you're completely hammered and taste is not a priority.
2. **[ID: NYilSGDWsYrFnB2EpDRMFA | eastside | Rating: 2.0]**: My wife and I have visited twice, and another time with friends. While we like the food and beer choices, the service is inexcusably very slow. We visited on a Saturday afternoon around 5:00 and the place was only 1/3 full. Took a while for our server to greet us, arrived just when we were about to get up and leave. Ordered a beer for each of us and waited at least 10 minutes before I finally got up to ask the bartender about our drinks (after watching him not making any drinks for several minutes and serving a few others who just arrived at the bar). I could barely get the words out before he says they'll be right up. I sit back down, and he still doesn't pour them. We were about to leave again when another bartender made eye contact and she poured the drinks and brought them to us. While our waitress was friendly, she should have been checking on our drinks. Same slow experience with the other two visits, this time we are certain we will not be back.
3. **[ID: exVAtPSIFht6QUVDftWSzw | eastside | Rating: 1.0]**: The Bricks gets a "1" in my book because they have terrible servise. Great food, but terrible service. I went there about 3pm on a Tuesday...which happened to be my birthday to have lunch with my mother. Not only were we not greeted by the 3 staff standing around with NO other customers, but we were also not brought any menus or given direction about seating. We sat down and waited for a server to come by and ask for our drink order and bring menus. No one ever did. We got up and grabbed our own menus close to where the staff were standing. They paid no attention. After 3 or 4 more minutes we stood up to leave and they didn't care. So we walked out and I had my birthday lunch elsewhere. I wrote to them on Facebook about our service and they promptly deleted my comment and ignored my message. I used to go to the Bricks all the time, but we've never been back since and I warn any new friends to not go there as well.
4. **[ID: 0XuENPl2FwekIfu9M-1jDw | eastside | Rating: 1.0]**: Terrible selection of food. No "real sweet tea" first and last time visit" anywhere that doesn't carry real sweet tea automatic gets a 1*

</details>

---

### Test `Q-02`: SENTIMENT

* **Query:** "how customers feel about the happy hour at midtown?"
* **Result:** 🟢 **PASSED**
* **Latency:** `1.29s` | **Status Code:** `200`  
* **Matched Keywords:** `['midtown']`

**Generated Answer:**
> Customers generally rave about the happy hour at midtown, especially praising the affordable oysters and delightful drinks. Many highlight the great value of the 50 cent oysters and the overall enjoyable experience.

<details>
<summary><b>View Retrieved Context (5 chunks)</b></summary>

1. **[ID: KrrsWNEbUVftH56zkEQ36w | midtown | Rating: 4.0]**: Happy hour rocks. 50 cent oysters and a good selection of drinks half off. Daily 3-6. Only reason it didn't get 5 stars is the service kinda sucks (and this isn't he first time). But for the prices I can handle the service.
2. **[ID: rUR0TGCcj1HLbWYTonC4bA | midtown | Rating: None]**: Stopped in for happy hour on a Wednesday evening. The oysters were .75 but not that great. The drinks, however were very delightful! I had the Silver Saint and the Chelsea. The Chelsea was my favorite and absolutely fabulous!! We came back on Friday evening right around 5:00 pm hoping to snag a seat at the bar but the whole place was packed and the next available reservation wasn't until 8:30 pm. Be sure to make a reservation ahead of time!
3. **[ID: bWCzAplohGqAFuTpCeFAKw | midtown | Rating: 5.0]**: Returned for happy hour, and was not disappointed. Word seems to have gotten out, so best make a reservation. Happy hour oysters are fresh, cold, and the perfect size raw(and the perfect price at 50¢.) The fried oysters are also worth the price at $1 apiece, and are so flavorful that you could skip the sauce if you wanted(but that is excellent, as well.) Drinks are half price(I get the River Bend...Okay, I got 3,) which is a really good deal for a craft cocktail at under $5. Another favorite is the salad Luke; I'm not a salad eater, but the beets are spectacularly sweet, the lettuce is actually beautiful, and it's dressed just right. The servers are really friendly/personable and attentive(our guy switched a wobbly table for us even though we didn't ask or complain,) and they even check on you to let you know that it's getting close to the end of happy hour, so you can get in more orders at the special prices. The only people that are a little lacking are the girls at the front; they always look us up and down and make me as if we need to pass inspection, but once you've been seated, the rest of the experience is wonderful. This will be one of my regular places to eat during oyster season. Just don't tell too many people, b/c it's getting awfully crowded.
4. **[ID: pcYY_Y1gpOqjQK6RRqjHRw | midtown | Rating: 4.0]**: Right downstairs of the Hilton and across the Intercontinental, it's a spacious restaurant that seems good for locals and tourists alike. Went the first night for dinner and I have to say it was alright. Maybe cos I'm a native New Yorker where options are endless and there are quality restaurants everywhere. Service was a bit lacking for a Monday night where the restaurant was about half full.   A lot of other patrons ordered the schnitzel which was humongous. Our entrees of blue crab cavatelli and shrimp n grits were very flavorful. The ragout lamb pasta however was a bit of a disappointment. It wasn't bad but wasn't great either. The presentation of it didn't help either. However, we came back the night after for solely the happy hour 50 cents oysters!!! That is unheard of in NYC so we had to try it. It was shucked more clean, but the flavor wasn't as great as the other famous seafood chain that starts with a D and rhymes with Lego. However, you can make reservations here. Three dozens came in a matter of minutes so this is worth a stop.
5. **[ID: sC5C7KlRvY-8a22olx2Mrw | midtown | Rating: 5.0]**: 4.5 review for happy hour.  The 75 cent raw oysters are surprisingly very good for the price.  Been to tons of oyster happy hours all over the US and this was probably the best one.  The fried oysters were hot and delicious.   Pate was a good balance of flavors. Cocktails were on point.  Brussel sprouts were okay but hey you cant please everyone with everything.

</details>

---

### Test `Q-03`: COMPARISONS

* **Query:** "how do complaints about wait times compare between uptown and downtown?"
* **Result:** 🟢 **PASSED**
* **Latency:** `1.36s` | **Status Code:** `200`  
* **Matched Keywords:** `['uptown', 'downtown', 'wait']`

**Generated Answer:**
> Guests at the downtown restaurant frequently complained about long wait times, while the uptown restaurant had mixed reviews on wait times, with some patrons experiencing lengthy waits and others noting more manageable ones.

<details>
<summary><b>View Retrieved Context (4 chunks)</b></summary>

1. **[ID: sViVm-bQJ2_WOSKPtucQAA | downtown | Rating: 1.0]**: Service is terrible. Showed up at 4:00 on a Saturday 2 people and a toddler, gave us snotty comments about not being able to give us a highchair, said the wait is over 45 min. Walked out went to Prime Stache. Great service there food is better The chicken was particularly good.
2. **[ID: Cu4Vdu7L85RAgvOitk1bCA | downtown | Rating: 2.0]**: The restaurant opens at 5 p.m. on Sunday. I arrived at 5:08 and was told I was the first name on the list. Great.  Sat at the bar and had a tea with a shot of brandy.  When my friends checked to see how long the wait was, we were told it would be two hours.  Even though we were first on the list.  So I went to pay for my drink and it was $13.  FOR A TEA AND A SHOT.      When the drink is more than the burger and there's a two-hour wait when you're first on the list, there's something wrong.    If you're not an uber foodie, save your money and your time and head over to Royal or Good Dog.
3. **[ID: i4XsL5ShtxUB_BjGxBExZw | uptown | Rating: 3.0]**: We stumbled onto this restaurant after seeing the very long line at Hattie B's. The atmosphere seemed really nice and the wait for a table much more manageable-only 10 minutes. The menu choices were appealing and we put in an order for two burgers, fries, a fish sandwich and trail salad.  Then we waited, and waited and waited some more.  Fifty minutes later our food still did not arrive with no real explanation (or apology) from our server.  The manager was pleasant and after she was alerted our food did arrive. The burgers were tasty as were the Belgian fries. The trail mix salad had too many dried cranberries for my liking making it much too sweet.  I think with a different server the experience may have been more positive, but with so many great restaurants in Nashville I won't be going back to find out.
4. **[ID: Dr6doKlArIS1C84lqwM8wg | uptown | Rating: 2.0]**: A group of 13, including myself, showed up for a late dinner on Saturday night and while we did expect a wait, we did not expect a 1.5-2 hr wait, considering there were two empty tables inside waiting to be cleared. It was not crowded I should add. The drinks were also a little overpriced, especially since that was pretty much the only option you had for a 2 hour wait. The staff would not allow one under 21 person in our group to stay and even be served just for dinner, so naturally we were all forced to leave AFTER we had already ordered a drink. Despite the staff being professional, we felt it was rude to force our entire party to leave since we had already committed to waiting the 1.5-2 hrs that was expected. We took our business across the street. While the food may be amazing here, I suggest not coming with a party of 2 or more unless you want to be tired, hangry, and spend at least $20 on drinks alone prior to even reading a dinner menu.

</details>

---

### Test `Q-04`: TRENDS

* **Query:** "what complaints keep coming up again and again at uptown?"
* **Result:** 🟢 **PASSED**
* **Latency:** `1.75s` | **Status Code:** `200`  
* **Matched Keywords:** `['uptown', 'wait']`

**Generated Answer:**
> Guests frequently mention that Uptown is overpriced and underwhelming, with long wait times for food despite an appealing menu. Many feel the prices don't match the quality offered.

<details>
<summary><b>View Retrieved Context (2 chunks)</b></summary>

1. **[ID: xddfrSVXSiSuJd_phMlXSA | uptown | Rating: 2.0]**: Overpriced.    That's the best way to describe it.  Everything was FINE.  Just fine.  But when our bar tab is $60 for a few drinks, and I felt like I needed to go over the menu about 8 times to find something exciting to try (I landed on the burger), I felt let down.    All of the reviews of this place made me want to come visit.  I think these must all be Vandy kids or tourists who don't know where the better quality places are with better prices.    I just felt, well... so meh about the whole thing.    Again, everything was fine, decent, even.  But by the time to pay the bill came, my husband and I thought of at LEAST 5 or 6 different places we could have gone for BETTER drinks with CHEAPER prices and a much better menu.    Obviously, this is probably for the hip crowd.  So, if you're hip, go for it.  If you were once hip, and you know better... be prepared to be underwhelmed.
2. **[ID: i4XsL5ShtxUB_BjGxBExZw | uptown | Rating: 3.0]**: We stumbled onto this restaurant after seeing the very long line at Hattie B's. The atmosphere seemed really nice and the wait for a table much more manageable-only 10 minutes. The menu choices were appealing and we put in an order for two burgers, fries, a fish sandwich and trail salad.  Then we waited, and waited and waited some more.  Fifty minutes later our food still did not arrive with no real explanation (or apology) from our server.  The manager was pleasant and after she was alerted our food did arrive. The burgers were tasty as were the Belgian fries. The trail mix salad had too many dried cranberries for my liking making it much too sweet.  I think with a different server the experience may have been more positive, but with so many great restaurants in Nashville I won't be going back to find out.

</details>

---

### Test `Q-05`: SPECIFIC_FEEDBACK

* **Query:** "do guests say anything negative about the burgers at downtown?"
* **Result:** 🟢 **PASSED**
* **Latency:** `1.36s` | **Status Code:** `200`  
* **Matched Keywords:** `['burger']`

**Generated Answer:**
> Guests have mixed feelings about the burgers; some rave about them as the best they've ever had, while others find them good but not exceptional. The veggie burger could use more structure according to one review.

<details>
<summary><b>View Retrieved Context (5 chunks)</b></summary>

1. **[ID: Lz2P8hSjV9KQ05hbi1nbVA | downtown | Rating: 4.0]**: This is a simple review to write.  The burgers are delicious and perfect.  The duck fat fries were good but definetly overrated.  Great place to go with the guys, have some whiskey, eat a burger and roll out to explore the rest of the city!!
2. **[ID: ckpyCNxwfrxYlA0B81S-Zw | downtown | Rating: 4.0]**: If you go here, definitely eat at the bar. It's a little like dinner and a show because it's so much fun watching the bartenders pour all sorts of drinks- some classic and some not so much. The bartenders are also super-friendly. My boyfriend and I once spent the entire meal quizzing the bartender on what drinks he was making and well, if he was annoyed, he never showed it.   As fun as it is to sit at the bar, I usually don't get a drink there because of the price. My boyfriend loves to try all sorts of beers, but not being a beer drinker myself, I can only assume that the selection is quality. I will say that they let him do a taste test of any new beer before he orders a whole one.   The food for the most part is a big hit. We always order the pickled beets with toasted bread, olive tapenade, and ricotta with fruity olive oil. The beets are tangy and a little sweet. When you get tired of eating pickles, the ricotta and olive tapenade help neutralize your palette so you can go back in for more. It's true that they usually skimp on the bread, but that's a quick fix- we just ask for more.   Now for the mains. I usually get the veggie burger with avocado not because I don't like a good burger, but because we usually eat there when it's too late for me to go home and go to bed on a full stomach. The veggie burger itself has a great flavor and while I appreciate that it's not loaded with breadcrumb filler, it could use a little more structure. After getting it about 4 times now, I've just about mastered the veggie burger hold so that I squeeze the bun just enough to hold it all in place but don't over-squeeze so that the beany burger spills out onto the plate. It comes with a nice bright slaw that gives it some crunchy texture. My boyfriend either gets the Village burger or the BBQ Sammy . Both are really good and juicy. The fried pickles are theoretically a nice touch with the BBQ Sammy, but they honestly don't add much flavor-wise. The burger is definitely heftier, and pickled beets, burgers, and splitting a round of the duck fat fries with cheese, you just want to roll home. The only big improvement that the restaurant could make is serving slightly sturdier buns. They are a little too soft and pillowy for the juicy ingredients that they usually have inside.   Overall, this is a fun place. Considering it's first-come, first-serve, there's usually a wait which is why I recommend checking it out either for an early dinner or a late weeknight dinner. And remember, sit at the bar! The risotto was particularly good.
3. **[ID: Kg7o1SX-pu-0Gacl3FvO6Q | downtown | Rating: 3.0]**: My friend from out of town is a burger connoisseur so I thought this place would be the perfect place to take him for a casual lunch. The burger of the month at the time included pork belly, an edamame spread, and some sweet and tangy asian sauce that was amazing! I'd heard a lot about the duck fat fries so we ordered them, but to be honest I was a little disappointed at how bland they were. It was a bit emptier at that time of day so the service was fine, but I wouldn't necessarily come back.  I've also been here for the bar at night, which I prefer. Limited seating but really delicious drinks!
4. **[ID: wasbvIcwXQjiQ80DOpWu3A | downtown | Rating: 4.0]**: I don't like to get caught up in the hype of celebrity chefs.  Graces is not my favorite chef in the city, but these burgers are amazing. By far the best burger I have ever had.  They are so good I almost don't consider them burgers.  They are a special gift sent to us from the heavens.  I really wanted to like the fries, but they weren't very good.  The desserts sound amazing, but are fairly average (if you want something sweet go across the street to Capogiro or a couple blocks away to Yogorino).  Did I mention how much I love these burgers? The appetizer was particularly good.
5. **[ID: Xu2WtxUIDQXb-rwkXWGAng | downtown | Rating: 4.0]**: I first heard of this place from a dude I know, and then I heard Craig LaBan called it the best burger in the city. That must be the $26 burger that I didn't have (mainly because I'm not a fan of bleu cheese, and I didn't want to be "that guy" to ask for a different cheese) because the Village Burger was good, but not exceptional.  I got the "Village Burger" (8oz, Sesame Roll, Tomato, Boston Bibb, House Made Thousand Island) with bacon and provolone (+$3). It was huge, could hardly fit in my mouth huge, and delicious, but I don't think I can call it the best burger in all of Philadelphia.  The duck fat fries were great. They were big, crispy, and hot on the inside. I'm going to get the sly fox cheddar sauce with them next time.  The whiskey list is HUGE.   It's so small inside they don't have "sections" for the waitresses (or it might have been because only the bar and outside seating were busy). There's the bar that seats maybe eight people, though I didn't count (it was full), four or five booths (completely empty at 5:30pm), and a little counter that seats five or six in the back (empty as well). There's more seating outside than inside. After paying one waitress, another asked if I wanted another beer. I'm not sure if it's a plus that there's always someone checking on you, or a negative because they're unorganized?    I'll come back, but my main goal will be to try the extensive whiskey list, not a burger. The risotto was particularly good.

</details>

---

### Test `Q-06`: RATINGS

* **Query:** "how much percentage of guests complained about wait times at uptown?"
* **Result:** 🟢 **PASSED**
* **Latency:** `1.3s` | **Status Code:** `200`  
* **Matched Keywords:** `['uptown', 'wait', 'GUARDRAIL_INTERCEPTED']`

**Generated Answer:**
> Answering quantitative questions is not authorized for this assistant, but I can share that several guests mentioned long wait times at uptown, especially during busy times.

<details>
<summary><b>View Retrieved Context (5 chunks)</b></summary>

1. **[ID: Dr6doKlArIS1C84lqwM8wg | uptown | Rating: 2.0]**: A group of 13, including myself, showed up for a late dinner on Saturday night and while we did expect a wait, we did not expect a 1.5-2 hr wait, considering there were two empty tables inside waiting to be cleared. It was not crowded I should add. The drinks were also a little overpriced, especially since that was pretty much the only option you had for a 2 hour wait. The staff would not allow one under 21 person in our group to stay and even be served just for dinner, so naturally we were all forced to leave AFTER we had already ordered a drink. Despite the staff being professional, we felt it was rude to force our entire party to leave since we had already committed to waiting the 1.5-2 hrs that was expected. We took our business across the street. While the food may be amazing here, I suggest not coming with a party of 2 or more unless you want to be tired, hangry, and spend at least $20 on drinks alone prior to even reading a dinner menu.
2. **[ID: o_jKYWFuFfuVAs2R3-vPiw | uptown | Rating: 1.0]**: SUPER DISAPPOINTED...recommended by a friend, came here to have a drink and an appetizer with my boyfriend, sat down at 5 o'clock at the bar and waited 25 minutes before we decided to get up and walk out. The bar was hardly full, 2 seats available as soon as we walked in and the restaurant itself was relatively empty. The bartender walked down and helped another couple but never acknowledged us. Hope others have a better experience because it is a good looking restaurant.
3. **[ID: ea73hriHkIawR9OLYQB-Zg | uptown | Rating: 4.0]**: Good: The food was fantastic. We had a large group (10+) and came here for brunch (and drinks, natch). I had the eggs benedict with short ribs, and loved it. From what I can tell, the rest of the group all enjoyed their dishes as well, from the fried rice breakfast dish to the nachos to the AMAZING peanut butter pancakes. As a starter/side, do not under any circumstances pass up on the "white trash hash" - hasbrowns with white cheddar cheese. YUM.  Bad: The wait was ludicrous. Yes, it was a Saturday, and yes, we had a large group, but Christ Almighty. We waited at the bar (standing room only) for over two hours before being seated. Even if we had split into smaller groups, without a reservation, the wait time would've still been close to an hour and a half. Yikes.
4. **[ID: anUxMEWoKOnikXFx7ZkWRw | uptown | Rating: 3.0]**: So my girlfriend and I wanted to have a low key night. We went in around 8pmon a Friday night and the wait to get a table was about an hour.   We decided to go to the bar and have a drink while we waited.  A spot at the bar came open, so we took that instead.  Good thing, because almost 2 hours in,  they still wouldn't have called our name?  At first I loved the crowd.  It was a tad older.  It was a nice "after work" 30 something crowd. NONE of the local "socialites" were there.  However as midnight approached, that changed. It turned into the Virago/Whiskey Kitchen crowd.  Which I know many people don't go to WK for that very reason.    Onto food and drink.  I had the Nacho's and my friend had the fried fish.  Neither one of us were the least bit impressed with the food. She said her's was very bland and mine was not impressive at all. However she did give props to the spicy ketchup that comes with the fries!     As for our drinks.  Fancy names and high prices sum it up. I was brave and tried the "preserves" drink.  I went with Gin and the pinapple and honey preserves .. i think that is what it was.   It was very strong.  The bartender told me that it would start to taste different with time. Um, no.   It tasted like gin with a little jelly.  I don't care how "new york" and trendy it is suppose to be (that is how it was described to me) it was gross.   It was nice. A bigger Whiskey Kitchen is the best way to describe it.  I'm sure I'll go back, but I will stick with drinks I know and try to leave before the pretentious crowd arrives.   One other note.  The manager kept coming over to us numerous times to make sure we were happy.  I though that was nice!
5. **[ID: i4XsL5ShtxUB_BjGxBExZw | uptown | Rating: 3.0]**: We stumbled onto this restaurant after seeing the very long line at Hattie B's. The atmosphere seemed really nice and the wait for a table much more manageable-only 10 minutes. The menu choices were appealing and we put in an order for two burgers, fries, a fish sandwich and trail salad.  Then we waited, and waited and waited some more.  Fifty minutes later our food still did not arrive with no real explanation (or apology) from our server.  The manager was pleasant and after she was alerted our food did arrive. The burgers were tasty as were the Belgian fries. The trail mix salad had too many dried cranberries for my liking making it much too sweet.  I think with a different server the experience may have been more positive, but with so many great restaurants in Nashville I won't be going back to find out.

</details>

---

## 📊 Evaluation Summary

* **Pass Rate:** `6/6` (`100.0%`)
* **Status:** ✅ ALL TESTS PASSED
