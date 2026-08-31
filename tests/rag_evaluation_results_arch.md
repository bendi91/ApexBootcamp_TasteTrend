# 🧪 RAG Pipeline Evaluation Report

**Target API:** `https://e1qjr4le51.execute-api.eu-central-1.amazonaws.com/poc/query`  
**Timestamp:** `2026-08-24 15:54:12`

---

### Test `Q-01`: RATINGS

* **Query:** "typical ratings at eastside res?"
* **Result:** 🟢 **PASSED**
* **Latency:** `1.66s` | **Status Code:** `200`  
* **Matched Keywords:** `['rating', 'star', 'eastside', 'review']`

**Generated Answer:**
> Guests typically give eastside restaurant ratings around 3 to 4 stars, appreciating the atmosphere and service but noting mixed reviews about the food quality.

<details>
<summary><b>View Retrieved Context (3 chunks)</b></summary>

1. **[ID: dDKRtNXR8JJAz4x_ZCGo3g | eastside | Rating: 4.0]**: Great location, cool atmosphere! The food was a fairly priced for the quality, which was good. I had the pulled pork tacos and they were not skimpy, fully stuffed and filling for $6. Great draft beer selection but it was a buck or two overpriced compared to other craft beer places. The two waitresses were very nice and pleasant. It was slow when we got there and them boom it was packed, they didn't forget about us but we did have to track her down for our last beer. I will be back for sure!
2. **[ID: ADodUkepU3OyY-G5zZk7yA | eastside | Rating: 3.0]**: This place is fun! I like the staff and the vibe. Food is okay. Beer selection is okay. Great happy hour on wine once a week. 3.5 stars is more appropriate for this place.
3. **[ID: BCLvpd08Ci4Tcq-fIRhZdA | eastside | Rating: 2.0]**: Leaving this 2-star review in response to the food, not the place as a drinking/hangout spot...although the wine was crap, too. 2-Stars awarded for the Nintendo 64 and all of the nostalgia-worthy games, the decent choice of drafts (even if they were out of the draft I ordered), and the great service from the staff. The food, on the other hand, will make you wish you had eaten at home. My wife and I went out as a treat because we didn't feel like cooking, but the majority of our food was sub-par. I got the shrimp po-boy which was not a po-boy by definition (it was just shrimp on a crappy sandwich...no French bread, no Cajun sauce or even enough Cajun seasoning, and the shrimp was obviously frozen-thawed not fresh). One of the shrimps was even gray when I bit into it, and the sandwich itself smelled more like old fish than fresh shrimp. My wife got the Athena chicken sandwich and that was just so-so, with the overwhelming taste of feta disguising the low-quality factory chicken they use for the sandwich. The best part of our collective meals was the mixed greens we ordered as a side, so I wouldn't exactly recommend ordering food here unless you're completely hammered and taste is not a priority.

</details>

---

### Test `Q-02`: SENTIMENT

* **Query:** "how customers feel about the happy hour at midtown?"
* **Result:** 🟢 **PASSED**
* **Latency:** `1.41s` | **Status Code:** `200`  
* **Matched Keywords:** `['midtown', 'happy hour', 'service']`

**Generated Answer:**
> Customers generally rave about the happy hour at midtown, especially praising the 50 cent oysters and the variety of half-off drinks. While some mention service issues, the overall sentiment is very positive, highlighting the great value and quality of the offerings.

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

* **Query:** "which spot is better if i want good vegetarian options, eastside or downtown?"
* **Result:** 🟢 **PASSED**
* **Latency:** `2.02s` | **Status Code:** `200`  
* **Matched Keywords:** `['vegetarian', 'veggie', 'eastside', 'downtown']`

**Generated Answer:**
> Based on the reviews, downtown seems to offer better vegetarian options with its veggie burger and other plant-based dishes. Eastside focuses more on meat-centric offerings.

<details>
<summary><b>View Retrieved Context (4 chunks)</b></summary>

1. **[ID: nAdvLArVs5EaKwrOvFXTuQ | eastside | Rating: 5.0]**: I ordered the bird and pig with Asian slaw.. $10.   The sandwich is warm and pressed.  It has pulled chicken inside.  I was worried it would be dry.  IT'S NOT.  Very moist!  Thick cut bacon and thinly sliced green apple.there was also a mayo type sauce. .tasted a bit sweet...Boy was this sandwich great!!  The Asian slaw was delicately dressed with the careful handed use of sesame oil.   Fantastic!   And they have a large assortment of Florida brewed beers.  The Wynwood iPA was so flavorful and foam on top just pillowy.  Atmosphere relaxed.  Staff is friendly and service great.  I was here on a Thursday night about 6pm.  Nice and clean.
2. **[ID: 94N0yL4NknDfB4JITXlUWA | eastside | Rating: 4.0]**: Just went there yesterday for brunch...  I've had a ton of grilled cheese sandwiches but this makes my top five. Loved the atmosphere. So happy we gave this restaurant a chance.
3. **[ID: KlfoquzypG2Jug3R9v7dCA | downtown | Rating: 3.0]**: Disclaimer: this three star review is from a vegetarian's perspective.  I understand that this place is in contention for best (real) burger in the city.   My (carnivorous) friend was looking for someone to join her for lunch at Village Whiskey so I figured I'd give their veggie burger a try.  It was a standard spicy black bean burger...it was good but I won't ever need to go back again.  My friend seemed to enjoy her burger and the duck fat fries.  I didn't try the fries (quack quack) despite how amazing they smelled.   It was a decent lunch but definitely a place for meat-eaters.
4. **[ID: ckpyCNxwfrxYlA0B81S-Zw | downtown | Rating: 4.0]**: If you go here, definitely eat at the bar. It's a little like dinner and a show because it's so much fun watching the bartenders pour all sorts of drinks- some classic and some not so much. The bartenders are also super-friendly. My boyfriend and I once spent the entire meal quizzing the bartender on what drinks he was making and well, if he was annoyed, he never showed it.   As fun as it is to sit at the bar, I usually don't get a drink there because of the price. My boyfriend loves to try all sorts of beers, but not being a beer drinker myself, I can only assume that the selection is quality. I will say that they let him do a taste test of any new beer before he orders a whole one.   The food for the most part is a big hit. We always order the pickled beets with toasted bread, olive tapenade, and ricotta with fruity olive oil. The beets are tangy and a little sweet. When you get tired of eating pickles, the ricotta and olive tapenade help neutralize your palette so you can go back in for more. It's true that they usually skimp on the bread, but that's a quick fix- we just ask for more.   Now for the mains. I usually get the veggie burger with avocado not because I don't like a good burger, but because we usually eat there when it's too late for me to go home and go to bed on a full stomach. The veggie burger itself has a great flavor and while I appreciate that it's not loaded with breadcrumb filler, it could use a little more structure. After getting it about 4 times now, I've just about mastered the veggie burger hold so that I squeeze the bun just enough to hold it all in place but don't over-squeeze so that the beany burger spills out onto the plate. It comes with a nice bright slaw that gives it some crunchy texture. My boyfriend either gets the Village burger or the BBQ Sammy . Both are really good and juicy. The fried pickles are theoretically a nice touch with the BBQ Sammy, but they honestly don't add much flavor-wise. The burger is definitely heftier, and pickled beets, burgers, and splitting a round of the duck fat fries with cheese, you just want to roll home. The only big improvement that the restaurant could make is serving slightly sturdier buns. They are a little too soft and pillowy for the juicy ingredients that they usually have inside.   Overall, this is a fun place. Considering it's first-come, first-serve, there's usually a wait which is why I recommend checking it out either for an early dinner or a late weeknight dinner. And remember, sit at the bar! The risotto was particularly good.

</details>

---

### Test `Q-04`: TRENDS

* **Query:** "the complaints about long wait times at uptown increased or not?"
* **Result:** 🟢 **PASSED**
* **Latency:** `1.56s` | **Status Code:** `200`  
* **Matched Keywords:** `['busy', 'uptown', 'long', 'wait']`

**Generated Answer:**
> Complaints about long wait times at Uptown have been frequent, with several reviews mentioning extended waits of up to 2 hours or more, especially when the restaurant wasn't very busy. Some guests felt the wait was justified, but others found it excessive and disruptive.

<details>
<summary><b>View Retrieved Context (5 chunks)</b></summary>

1. **[ID: Dr6doKlArIS1C84lqwM8wg | uptown | Rating: 2.0]**: A group of 13, including myself, showed up for a late dinner on Saturday night and while we did expect a wait, we did not expect a 1.5-2 hr wait, considering there were two empty tables inside waiting to be cleared. It was not crowded I should add. The drinks were also a little overpriced, especially since that was pretty much the only option you had for a 2 hour wait. The staff would not allow one under 21 person in our group to stay and even be served just for dinner, so naturally we were all forced to leave AFTER we had already ordered a drink. Despite the staff being professional, we felt it was rude to force our entire party to leave since we had already committed to waiting the 1.5-2 hrs that was expected. We took our business across the street. While the food may be amazing here, I suggest not coming with a party of 2 or more unless you want to be tired, hangry, and spend at least $20 on drinks alone prior to even reading a dinner menu.
2. **[ID: i4XsL5ShtxUB_BjGxBExZw | uptown | Rating: 3.0]**: We stumbled onto this restaurant after seeing the very long line at Hattie B's. The atmosphere seemed really nice and the wait for a table much more manageable-only 10 minutes. The menu choices were appealing and we put in an order for two burgers, fries, a fish sandwich and trail salad.  Then we waited, and waited and waited some more.  Fifty minutes later our food still did not arrive with no real explanation (or apology) from our server.  The manager was pleasant and after she was alerted our food did arrive. The burgers were tasty as were the Belgian fries. The trail mix salad had too many dried cranberries for my liking making it much too sweet.  I think with a different server the experience may have been more positive, but with so many great restaurants in Nashville I won't be going back to find out.
3. **[ID: vY06Ye_udeTHL6rfnSZfCw | uptown | Rating: 2.0]**: Terrible wait (unnecessary), average service, above average prices, and excruciating wait for food. Find someplace else. There's lots to choose from.
4. **[ID: T9notipZzakxsGqZNrR2Fg | uptown | Rating: 5.0]**: First and foremost, this place is worth the wait. If you are planning to eat here, and didn't come before opening, expect at least a 20-30 minute wait if you're lucky. We got here right when the doors opened and only had to wait 20 minutes to get seated. The food is everything it's hyped up to be, and the service was really great. So, as said earlier, this place is worth the wait.
5. **[ID: 8hBiPbwlO6aKuGhkpj_20g | uptown | Rating: 3.0]**: Food was fantastic, service was so bad I wouldn't come back. They are severely understaffed, we finished eating 45 mins before we got the check. The hour and a half wait is completely unnecessary!

</details>

---

### Test `Q-05`: SPECIFIC_FEEDBACK

* **Query:** "the burgers are juicy at downtown?"
* **Result:** 🟢 **PASSED**
* **Latency:** `1.27s` | **Status Code:** `200`  
* **Matched Keywords:** `['burger', 'downtown']`

**Generated Answer:**
> Guests consistently praise the burgers at downtown for their juiciness and flavor. Many reviewers highlight the Village Burger as particularly delicious and satisfying.

<details>
<summary><b>View Retrieved Context (5 chunks)</b></summary>

1. **[ID: Lz2P8hSjV9KQ05hbi1nbVA | downtown | Rating: 4.0]**: This is a simple review to write.  The burgers are delicious and perfect.  The duck fat fries were good but definetly overrated.  Great place to go with the guys, have some whiskey, eat a burger and roll out to explore the rest of the city!!
2. **[ID: ckpyCNxwfrxYlA0B81S-Zw | downtown | Rating: 4.0]**: If you go here, definitely eat at the bar. It's a little like dinner and a show because it's so much fun watching the bartenders pour all sorts of drinks- some classic and some not so much. The bartenders are also super-friendly. My boyfriend and I once spent the entire meal quizzing the bartender on what drinks he was making and well, if he was annoyed, he never showed it.   As fun as it is to sit at the bar, I usually don't get a drink there because of the price. My boyfriend loves to try all sorts of beers, but not being a beer drinker myself, I can only assume that the selection is quality. I will say that they let him do a taste test of any new beer before he orders a whole one.   The food for the most part is a big hit. We always order the pickled beets with toasted bread, olive tapenade, and ricotta with fruity olive oil. The beets are tangy and a little sweet. When you get tired of eating pickles, the ricotta and olive tapenade help neutralize your palette so you can go back in for more. It's true that they usually skimp on the bread, but that's a quick fix- we just ask for more.   Now for the mains. I usually get the veggie burger with avocado not because I don't like a good burger, but because we usually eat there when it's too late for me to go home and go to bed on a full stomach. The veggie burger itself has a great flavor and while I appreciate that it's not loaded with breadcrumb filler, it could use a little more structure. After getting it about 4 times now, I've just about mastered the veggie burger hold so that I squeeze the bun just enough to hold it all in place but don't over-squeeze so that the beany burger spills out onto the plate. It comes with a nice bright slaw that gives it some crunchy texture. My boyfriend either gets the Village burger or the BBQ Sammy . Both are really good and juicy. The fried pickles are theoretically a nice touch with the BBQ Sammy, but they honestly don't add much flavor-wise. The burger is definitely heftier, and pickled beets, burgers, and splitting a round of the duck fat fries with cheese, you just want to roll home. The only big improvement that the restaurant could make is serving slightly sturdier buns. They are a little too soft and pillowy for the juicy ingredients that they usually have inside.   Overall, this is a fun place. Considering it's first-come, first-serve, there's usually a wait which is why I recommend checking it out either for an early dinner or a late weeknight dinner. And remember, sit at the bar! The risotto was particularly good.
3. **[ID: lKeXqrHUguxMSR7HWXcbrA | downtown | Rating: 4.0]**: Best burger in the city, hands down. The first time I had the Village Burger is was amazing and it hasn't disappointed since. What kills me is that on any given night, the wait to enjoy this tiny piece of meat heaven is unbearable. The solution? Go at lunch or really early in the afternoon if you can.   I honestly couldn't tell you how the other entrees are, because this is the only thing I get, along with the duck fat french fries of course. The appetizers are good, but nothing memorable. My 4 star rating really just stems from the burger and their cocktails. I've tried a few of them and all were really good.    Definitely try the pickle options too. My favorite was the pickled artichokes, but on last look at the menu, it looks like it was taken off.   Man, I think I need a burger right now... The fish was particularly good.
4. **[ID: wasbvIcwXQjiQ80DOpWu3A | downtown | Rating: 4.0]**: I don't like to get caught up in the hype of celebrity chefs.  Graces is not my favorite chef in the city, but these burgers are amazing. By far the best burger I have ever had.  They are so good I almost don't consider them burgers.  They are a special gift sent to us from the heavens.  I really wanted to like the fries, but they weren't very good.  The desserts sound amazing, but are fairly average (if you want something sweet go across the street to Capogiro or a couple blocks away to Yogorino).  Did I mention how much I love these burgers? The appetizer was particularly good.
5. **[ID: -X-RUh8n-GO7llo3wPyb7Q | downtown | Rating: 4.0]**: Nestled on the corner of 20th and Chestnut, it looks bigger than what you'll discover inside. A tight-knit community of tables, all filled, whether reservations can be made or not, saddled around a long bar, and some standing room to place your beer and food, if standing is fine.   Wander in at 6:00 on a Saturday, and are told its a 2 hour wait for a table. Bar is a much better option. Was able to grab a seat at the bar as soon as we got in.   Bartenders are friendly. The wall of whiskey (or whisky) behind the bar is quite impressive.   Food is quite delicious. Village burger with sauteed onions and blue cheese is quite the tasty treat. Burger is cooked a shade under what you request, which for medium, a bit redder is fine by me. The wife got a pulled pork sandwich, and salivated over every bite. A side order of duck fat fries in a cheese sauce compliments the meal well.   Pricing is surprisingly reasonable. Definitely on the list as a repeat place to go.

</details>

---

### Test `Q-06`: RATINGS

* **Query:** "show the average rating for eastside res?"
* **Result:** 🟢 **PASSED**
* **Latency:** `1.14s` | **Status Code:** `200`  
* **Matched Keywords:** `['GUARDRAIL_INTERCEPTED']`

**Generated Answer:**
> Answering quantitative questions is not authorized for this assistant, but I can share what guests typically say about their experience! Guests generally appreciate the fun atmosphere and friendly staff, though opinions on the food vary from good to sub-par.

<details>
<summary><b>View Retrieved Context (3 chunks)</b></summary>

1. **[ID: ADodUkepU3OyY-G5zZk7yA | eastside | Rating: 3.0]**: This place is fun! I like the staff and the vibe. Food is okay. Beer selection is okay. Great happy hour on wine once a week. 3.5 stars is more appropriate for this place.
2. **[ID: dDKRtNXR8JJAz4x_ZCGo3g | eastside | Rating: 4.0]**: Great location, cool atmosphere! The food was a fairly priced for the quality, which was good. I had the pulled pork tacos and they were not skimpy, fully stuffed and filling for $6. Great draft beer selection but it was a buck or two overpriced compared to other craft beer places. The two waitresses were very nice and pleasant. It was slow when we got there and them boom it was packed, they didn't forget about us but we did have to track her down for our last beer. I will be back for sure!
3. **[ID: BCLvpd08Ci4Tcq-fIRhZdA | eastside | Rating: 2.0]**: Leaving this 2-star review in response to the food, not the place as a drinking/hangout spot...although the wine was crap, too. 2-Stars awarded for the Nintendo 64 and all of the nostalgia-worthy games, the decent choice of drafts (even if they were out of the draft I ordered), and the great service from the staff. The food, on the other hand, will make you wish you had eaten at home. My wife and I went out as a treat because we didn't feel like cooking, but the majority of our food was sub-par. I got the shrimp po-boy which was not a po-boy by definition (it was just shrimp on a crappy sandwich...no French bread, no Cajun sauce or even enough Cajun seasoning, and the shrimp was obviously frozen-thawed not fresh). One of the shrimps was even gray when I bit into it, and the sandwich itself smelled more like old fish than fresh shrimp. My wife got the Athena chicken sandwich and that was just so-so, with the overwhelming taste of feta disguising the low-quality factory chicken they use for the sandwich. The best part of our collective meals was the mixed greens we ordered as a side, so I wouldn't exactly recommend ordering food here unless you're completely hammered and taste is not a priority.

</details>

---

## 📊 Evaluation Summary

* **Pass Rate:** `6/6` (`100.0%`)
* **Status:** ✅ ALL TESTS PASSED
