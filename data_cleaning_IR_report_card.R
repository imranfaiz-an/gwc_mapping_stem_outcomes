library(readxl)
library(tidyverse)
library(writexl)

math_prof <- read_excel("2025-Report-Card-Public-Data-Set.xlsx", sheet = "ELAMathScience")
colnames(math_prof)

math_prof <- math_prof %>% 
  filter(City == "Chicago") %>%
  select(RCDTS, Level, `School Name`, City, `% ELA Proficiency`, `% Math Proficiency`)

science_prof <- read_excel("2025-Report-Card-Public-Data-Set.xlsx", sheet = "ELAMathScience (2)")
colnames(science_prof)
science_prof <- science_prof %>%
  filter(City == "Chicago") %>%
  select(RCDTS, Level, `School Name`, City, `% Science Proficiency`)

math_and_science_prof <- left_join(math_prof,science_prof, by= c("RCDTS","School Name", "City","Level"))

write_xlsx(math_and_science_prof, "report_card_proficiency_scores.xlsx")
