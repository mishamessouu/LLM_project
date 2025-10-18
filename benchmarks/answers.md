# Benchmark: OurSQLBot vs gpt-5

## Question 1: According to the World Happiness Report, which country showed the greatest improvement in overall Happiness Score between 2015 and 2019?

**OurSQLBot (2905.3 ms)**  
According to the World Happiness Report, Venezuela showed the greatest improvement in overall Happiness Score between 2015 and 2019, with an increase of approximately 2.10 points. This significant rise suggests positive changes in various factors contributing to the happiness of its citizens during that period.

**gpt-5 (49093.3 ms)**  
Benin.

---

## Question 2: Based on the World Happiness Report, list the top 3 countries with the highest Social support for each year between 2015 and 2019.

**OurSQLBot (5089.2 ms)**  
Based on the World Happiness Report, here are the top 3 countries with the highest social support for each year from 2015 to 2019:

### 2015
| Country or Region | Social Support |
|-------------------|----------------|
| Iceland           | 1.40223        |
| Ireland           | 1.36948        |
| Denmark           | 1.36058        |

### 2016
| Country or Region | Social Support |
|-------------------|----------------|
| Norway            | 1.52242        |
| Finland           | 1.48701        |
| Denmark           | 1.47852        |

### 2017
| Country or Region | Social Support |
|-------------------|----------------|
| Norway            | 1.54036        |
| Iceland           | 1.48566        |
| Denmark           | 1.47883        |

### 2018
| Country or Region | Social Support |
|-------------------|----------------|
| Norway            | 1.58780        |
| Denmark           | 1.50161        |
| Iceland           | 1.48934        |

### 2019
| Country or Region | Social Support |
|-------------------|----------------|
| Finland           | 1.58780        |
| Denmark           | 1.57315        |
| Norway            | 1.55090        |

This table gives you a clear view of the countries that have been consistently high in social support across these years. If you have any more questions about the data or need further analysis, feel free to ask!

**gpt-5 (22819.0 ms)**  
I can do this, but to ensure it’s accurate I need to reference the official WHR datasets (2015–2016 use the “Family” component; 2017–2019 use “Social support”). Would you like me to fetch those datasets and compute the top 3 per year, or would you prefer I share a quick script you can run locally to generate the list?

---

## Question 3: From the World Happiness Report, show Denmark’s Happiness Score for each year between 2015 and 2019, and include the change from the previous year.

**OurSQLBot (5185.3 ms)**  
Here’s a summary of Denmark's Happiness Scores from the World Happiness Report for the years 2015 to 2019, along with the changes from the previous year:

| Year | Score | Change from Previous Year |
|------|-------|---------------------------|
| 2015 | 7.527 | None                      |
| 2016 | 7.526 | -0.001                    |
| 2017 | 7.522 | -0.005                    |
| 2018 | 7.555 | +0.033                   |
| 2019 | 7.600 | +0.045                   |

- **2015**: Denmark had a happiness score of **7.527**, which serves as the starting point with no previous data to compare.
- **2016**: The score slightly decreased to **7.526**, reflecting a change of **-0.001**.
- **2017**: The score dropped further to **7.522**, indicating a change of **-0.005** from the previous year.
- **2018**: There was an increase in happiness, with the score rising to **7.555**, showing a positive change of **+0.033**.
- **2019**: The upward trend continued, and the happiness score reached **7.600**, which is an increase of **+0.045** from 2018.

Overall, Denmark experienced fluctuations in its happiness score from 2015 to 2017, followed by a positive trend in 2018 and 2019.

**gpt-5 (44673.4 ms)**  
Here are Denmark’s reported happiness scores and year-over-year changes:

- 2015: 7.527 (change: n/a)
- 2016: 7.526 (change: -0.001)
- 2017: 7.522 (change: -0.004)
- 2018: 7.555 (change: +0.033)
- 2019: 7.600 (change: +0.045)

Source: World Happiness Report (2015–2019). Scores are on a 0–10 scale.

---

## Question 4: According to the World Happiness Report 2019, what was the average GDP per capita among the 10 happiest countries?

**OurSQLBot (2109.7 ms)**  
The average GDP per capita among the 10 happiest countries, according to the World Happiness Report 2019, is approximately 0.905. This value represents a normalized figure, where a higher number indicates a higher GDP per capita in relation to the countries included in the data set. This means that, on average, the happiest countries tend to have relatively high GDP per capita, which is often associated with better living standards and overall well-being.

**gpt-5 (76719.0 ms)**  
[error: Request timed out.]

---

## Question 5: Between 2015 and 2019, how did the average Healthy life expectancy score change overall according to the World Happiness Report?

**OurSQLBot (2924.4 ms)**  
The result you provided shows that the average healthy life expectancy score between 2015 and 2019 is approximately 0.625. This score is a numerical representation that reflects the overall health and well-being of the population in that period, as evaluated in the World Happiness Report.

To interpret this, a higher score typically indicates better health outcomes and longer life expectancy. However, since we only have this single average score, we can't determine the specific trend over the years from 2015 to 2019 (whether it increased or decreased year by year). If we had yearly data, we could analyze changes over time to see if healthy life expectancy was improving or declining during those years.

If you're looking for more specific insights or comparisons to prior years, please let me know!

**gpt-5 (64074.8 ms)**  
It rose slightly overall. From 2015 to 2019, the average Healthy life expectancy score increased modestly across countries in the World Happiness Report. If you’d like the exact change and year-by-year averages, I can compute those from the dataset you’re using.

---

## Question 6: In the 2018 World Happiness Report data, which countries had a Freedom to make life choices score above the global average?

**OurSQLBot (3021.1 ms)**  
In the 2018 World Happiness Report, several countries reported a Freedom to Make Life Choices score that exceeded the global average. Among the highlights are:

- **Finland**
- **Norway**
- **Denmark**
- **Iceland**
- **Switzerland**
- **Netherlands**
- **Canada**
- **New Zealand**

These nations are known for their high levels of personal freedom and overall well-being, contributing to their positive rankings in this category. The results reflect how citizens in these countries feel empowered to make personal decisions that impact their lives. If you need more details or specific countries from the additional rows, feel free to ask!

**gpt-5 (14946.3 ms)**  
I can compute that, but I need the actual 2018 World Happiness Report dataset you’re using (column names can vary by source). Please upload the CSV (often named 2018.csv) or confirm that I should use the common Kaggle version with a column named “Freedom to make life choices.”

If you’d like to run it yourself, here’s a quick way in Python (pandas):
- Load the file 2018.csv
- Compute the mean of the “Freedom to make life choices” column
- Filter countries with values above that mean

Example:
- Read CSV
- avg = mean(Freedom to make life choices)
- above = rows where Freedom to make life choices > avg
- Return the list of countries (optionally sorted)

If you share the file or confirm the exact dataset, I’ll return the precise country list and the global average.

---

## Question 7: According to the World Happiness Report 2019, what is the absolute difference in Happiness Score between the 1st and 10th ranked countries?

**OurSQLBot (2682.4 ms)**  
The World Happiness Report 2019 indicates that there is an absolute difference of approximately 0.523 in the Happiness Scores between the country ranked 1st and the country ranked 10th. This means that the top-ranked country has a Happiness Score that is 0.523 points higher than the 10th ranked country. This difference can give us insights into the relative levels of happiness among these countries.

**gpt-5 (8355.8 ms)**  
0.523 points

---

## Question 8: Which country was ranked as the happiest in the world in the 2017 World Happiness Report?

**OurSQLBot (2106.6 ms)**  
In the 2017 World Happiness Report, Norway was ranked as the happiest country in the world. This ranking is based on various factors that contribute to overall happiness, including economic stability, social support, and life expectancy, among others. Norway's strong emphasis on social welfare and quality of life is often highlighted as key contributors to its high happiness ranking.

**gpt-5 (2857.4 ms)**  
Norway.

---

## Question 9: Which country had the highest GDP per capita in 2019 according to the World Happiness Report?

**OurSQLBot (2076.9 ms)**  
In 2019, the country with the highest GDP per capita, according to the World Happiness Report, was Qatar. This indicates that in that year, Qatar had the highest income per person compared to other countries, contributing to its overall economic standing. If you have any more questions about GDP or other related topics, feel free to ask!

**gpt-5 (13863.3 ms)**  
Qatar.

---

## Question 10: According to the World Happiness Report, which country ranked lowest in Happiness Score in 2018?

**OurSQLBot (2276.7 ms)**  
According to the World Happiness Report, Burundi ranked the lowest in Happiness Score in 2018. This means that, based on various factors such as income, social support, and life expectancy, people in Burundi reported the lowest levels of happiness compared to other countries that year. If you have any more questions or need further information about this report or other countries' rankings, feel free to ask!

**gpt-5 (7573.7 ms)**  
Burundi.

---

