library(VennDiagram)
plotVennDiagrams <- function(dataframe, stage = 1) {
  dataframe <- dataframe %>% mutate(defsum = 0)
  dataframe <- dataframe %>% mutate(defsum = ifelse(RMW > 0 & HBT > 0 & BCI > 0, 3, ifelse(RMW > 0 & BCI > 0 |
                                                                                             RMW > 0 & HBT > 0 |
                                                                                             BCI > 0 & HBT > 0, 2,
                                                                                           ifelse(RMW > 0 | BCI > 0 | HBT > 0, 1,0))))
  noAKI <- dataframe %>% filter(defsum==0)
  dataframe <- dataframe %>% filter(defsum != 0)
  dataframe <- dataframe %>% group_by(patient_id) %>% top_n(1, defsum)
  dataframe <- dataframe %>% filter(duplicated(patient_id) == FALSE)


  df.RMW <- dataframe %>% filter(RMW > stage - 1 & HBT == 0 & BCI == 0)
  df.HBT <- dataframe %>% filter(HBT > stage - 1 & RMW == 0 & BCI == 0)
  df.BCI <- dataframe %>% filter(BCI > stage - 1 & RMW == 0 & HBT == 0)

  df.RMW_HBT <- dataframe %>% filter(RMW > (stage - 1) & HBT > (stage - 1) & RMW == 0)
  df.RMW_BCI <- dataframe %>% filter(RMW > (stage - 1) & BCI > (stage - 1) & HBT == 0)
  df.HBT_BCI <- dataframe %>% filter(HBT > (stage - 1) & BCI > (stage - 1) & RMW == 0)
  df.RMW_HBT_BCI <- dataframe %>% filter(RMW > (stage - 1) & HBT > (stage - 1) & BCI > (stage - 1))

  fit <- eulerr::euler(c("RMW" = nrow(df.RMW), "HBT" = nrow(df.HBT), "BCI" = nrow(df.BCI),
                         "RMW&HBT" = nrow(df.RMW_HBT), "HBT&BCI" = nrow(df.HBT_BCI), "RMW&BCI" = nrow(df.RMW_BCI), "RMW&HBT&BCI" = nrow(df.RMW_HBT_BCI)), shape = 'ellipse')
  return(fit)
}

plotAKIoverlap <- function(dataframe, stage = 1) {
  if ("aki" %in% colnames(dataframe)) {
    df.venn <- dataframe %>% select(patient_id, aki) %>% filter(aki == 1)
    draw.single.venn(area = length(unique(df.venn$patient_id)))
  } else if ("RMW" %in% colnames(dataframe)) {

    df.rmw <- dataframe %>% select(patient_id, RMW) %>% filter(RMW == 1)
    df.hbt <- dataframe %>% select(patient_id, HBT) %>% filter(HBT == 1)
    df.bci <- dataframe %>% select(patient_id, BCI) %>% filter(BCI == 1)

    s1 <- unique(df.rmw$patient_id)
    s2 <- unique(df.hbt$patient_id)
    s3 <- unique(df.bci$patient_id)

    draw.triple.venn(area1 = length(s1),
                     area2 = length(s2),
                     area3 = length(s3),
                     n12 = length(union(s1, s2)) - length(s1),
                     n23 = length(union(s2, s3)) - length(s2),
                     n13 = length(union(s1, s3)) - length(s3),
                     n123 = length(intersect(s2, intersect(s1, s3))),
                     fill = c("pink", "green", "orange"), lty = "blank", alpha = 0.5,
                     category = c("RMW", "HBT", "BCI"))

  }
}

plotAKIprediction <- function(dataframe, stage = 1) {

}
