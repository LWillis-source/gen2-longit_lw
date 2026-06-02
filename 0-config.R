# Custom RProfile for DADA2 analyses

rm(list=ls()) # clear environmental variables

# Load necessary packages
library(here) # current directory
library(dplyr) # dataframe manipulation
library(tidyverse) # transform data long/working form
library(ggplot2) # plotting
library(ggh4x) # ggplot2 extension for facet manipulation
library(cowplot)
library(viridis) # color scale
library(phyloseq) # phylogenetic tree
library(readxl) # read excel files
library(writexl) # write excel files
library(data.table) # manipulating matrices and tables
library(ggbeeswarm) # beeswarm
library(ggpubr) # add p-values to figures
library(rstatix) # wilcoxon test
library(factoextra) # PCA
library(MicrobiomeStat) # Diff abundance with LinDA
library(foreach) # Parallel and iterative processing
library(ggrepel) # ggplot2 text labels
library(scales) # scale labels
library(ggbreak) # break axes
library(Hmisc) # pearson correlation
library(ggtext) # custom text
library(readr)
library(purrr)
library(tidyr)
library(pheatmap)
library(stringr)
library(see)
library(gt) # pdf tables
library(ggdendro) # dendrograms
library(compositions) #clr
library(patchwork)
library(ggnewscale)
library(FAVA)

##########################
# Include custom functions
##########################

setup_metaphlan <- function(sample_sheet_path) {
  # Default Setup
  
  # import custom family colors
  colors <- read_excel(sample_sheet_path, sheet = 4)
  colors$Color <- paste0("#", colors$Color)
  
  # setup tables to populate phyloseq object
  seqtab_nochim <- read_excel(sample_sheet_path, sheet = 2)
  rownames(seqtab_nochim) <- seqtab_nochim$Feature
  seqtab_nochim <- seqtab_nochim %>% select(-Feature) %>%
    mutate(across(everything(), as.numeric))
  
  taxa <- read_excel(sample_sheet_path, sheet = 3)
  taxa <- taxa %>% mutate(fOTU = paste(Kingdom, Phylum, Class, Order, Family, sep = ";")) %>% # add fOTU
    mutate(Taxon = Species) %>%  #mapply(generate_taxon, Kingdom, Phylum, Class, Order, Family, Genus, Species)) %>% # add concise taxonomy name to plot
    mutate(Family2 = Family) %>% # add Family2 name to plot
    left_join(colors %>% select(fOTU, Color), by = c("fOTU")) # add Family colors 
  taxa_order <- taxa %>% arrange(match(Family, colors$Family)) # arrange taxa based on fOTU order in colors
  rownames(taxa) <- taxa$Feature # row names must match species.names
  taxa <- taxa %>% select(c("Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species", "fOTU", "Taxon", "Family2", "Color", "Feature"))
  taxa <- as.matrix(taxa) # taxa must be matrix
  
  samdf <- read_excel(sample_sheet_path, sheet = 1)
  samdf <- as.data.frame(samdf) # convert to dataframe
  rownames(samdf) <- samdf$Sample # change row names to be the sequencing name, remove "sample_"
  samdf <- samdf %>% select(-Sample) # remove Sample column
  
  # create phyloseq object
  ps <- phyloseq(otu_table(seqtab_nochim, taxa_are_rows = TRUE), sample_data(samdf), tax_table(taxa))
  
  return(list(ps = ps, taxa_order = taxa_order, samdf = samdf))
}


setup_tables_plants <- function(directory, sample_sheet_path) {
  # Default Setup
  
  # import custom family colors
  sheet_num <- 4
  colors <- read_excel(paste0(paste0(here(), '/1-data/Family_colors.xlsx')), sheet = sheet_num)
  colors$Color <- paste0("#", colors$Color)
  #colors <- colors %>% mutate(fOTU = paste(Kingdom, Phylum, Class, Order, Family, sep=";"))
  colors <- colors %>% mutate(Genus = factor(Genus, levels = rev(unique(colors$Genus)), ordered = TRUE))
  
  # Create phyloseq object that stores:
  # otu_table <- table of read counts for each ASV
  # tax_table <- taxonomic assignment of ASVs
  # sample_data <- metadata for all experiments
  # phy_tree <- phylogenetic tree from data
  
  # setup tables to populate phyloseq object
  seqtab_nochim <- readRDS(paste0(directory, 'seqtab_all.RDS')) # read in ASV read counts
  taxa <- read.table(paste0(directory,'feature_data.txt'), header = TRUE, sep = "\t") # read in ASV taxon info
  taxa <- taxa %>%
    mutate(Genus = ifelse(is.na(Genus), "NA", Genus)) %>%
    mutate(Family2 = ifelse(is.na(Genus), "NA", Genus)) %>% # add Family2 name to plot
    left_join(colors %>% select(Genus, Common_name, Color), by = c("Genus")) %>% # add Family colors 
    #mutate(Taxon = mapply(generate_taxon, Kingdom, Phylum, Class, Order, Family, Genus, Species)) %>% # add concise taxonomy name to plot
    mutate(Taxon = Common_name) %>%
    mutate(fOTU = Common_name) # add fOTU
  taxa_order <- taxa %>% arrange(match(Genus, colors$Genus)) # arrange taxa based on fOTU order in colors
  rownames(taxa) <- taxa$Sequence # row names must match species.names
  taxa <- taxa %>% select(c("Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species", "fOTU", "Taxon", "Family2", "Color", "Feature"))
  taxa <- as.matrix(taxa) # taxa must be matrix
  
  phy_tree <- read_tree(paste0(directory,'dsvs_msa.tree')) # read in phylogenetic tree
  samdf <- read_excel(paste0(here(), sample_sheet_path), sheet = 1) # Read in sample metadata
  samdf <- as.data.frame(samdf) # convert to dataframe
  rownames(samdf) <- sub('sample_', '', samdf$Sample) # change row names to be the sequencing name, remove "sample_"
  samdf <- samdf[2:ncol(samdf)] # remove Sample column
  
  # create phyloseq object
  ps <- phyloseq(otu_table(seqtab_nochim, taxa_are_rows = FALSE), sample_data(samdf), tax_table(taxa), phy_tree(phy_tree))
  
  # store DNA sequences in refseq slot of phyloseq object and rename taxa to short taxa names
  dna <- Biostrings::DNAStringSet(taxa_names(ps))
  names(dna) <- taxa_names(ps)
  ps <- merge_phyloseq(ps, dna)
  taxa_names(ps) <- sprintf("feature_%04d", seq_len(ntaxa(ps)))
  
  return(list(ps = ps, taxa_order = taxa_order, samdf = samdf))
}

setup_tables_meat <- function(directory, sample_sheet_path) {
  # Default Setup
  
  # import custom family colors
  sheet_num <- 3
  colors <- read_excel(paste0(paste0(here(), '/1-data/Family_colors.xlsx')), sheet = sheet_num)
  colors$Color <- paste0("#", colors$Color)
  colors <- colors %>% mutate(fOTU = paste(Kingdom, Phylum, Class, Order, Family, sep=";"))
  colors <- colors %>% mutate(fOTU = factor(fOTU, levels = rev(unique(colors$fOTU)), ordered = TRUE))
  
  # Create phyloseq object that stores:
  # otu_table <- table of read counts for each ASV
  # tax_table <- taxonomic assignment of ASVs
  # sample_data <- metadata for all experiments
  # phy_tree <- phylogenetic tree from data
  
  # setup tables to populate phyloseq object
  seqtab_nochim <- readRDS(paste0(directory,'seqtab_all.RDS')) # read in ASV read counts
  taxa <- read.table(paste0(directory,'feature_data.txt'), header = TRUE, sep = "\t") # read in ASV taxon info
  taxa <- taxa %>% mutate(fOTU = paste(Kingdom, Phylum, Class, Order, Family, sep=";")) %>% # add fOTU
    mutate(Taxon = mapply(generate_taxon, Kingdom, Phylum, Class, Order, Family, Genus, Species)) %>% # add concise taxonomy name to plot
    mutate(Family2 = ifelse(is.na(Family) | Family == "f__", Taxon, Family)) %>% # add Family2 name to plot
    left_join(colors %>% select(fOTU, Color), by = c("fOTU")) # add Family colors 
  taxa_order <- taxa %>% arrange(match(fOTU, colors$fOTU)) # arrange taxa based on fOTU order in colors
  rownames(taxa) <- taxa$Sequence # row names must match species.names
  taxa <- taxa %>% select(c("Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species", "fOTU", "Taxon", "Family2", "Color", "Feature"))
  taxa <- as.matrix(taxa) # taxa must be matrix
  
  phy_tree <- read_tree(paste0(directory,'dsvs_msa.tree')) # read in phylogenetic tree
  samdf <- read_excel(paste0(here(), sample_sheet_path), sheet = 1) # Read in sample metadata
  samdf <- as.data.frame(samdf) # convert to dataframe
  rownames(samdf) <- sub('sample_', '', samdf$Sample) # change row names to be the sequencing name, remove "sample_"
  samdf <- samdf[2:ncol(samdf)] # remove Sample column
  
  # create phyloseq object
  ps <- phyloseq(otu_table(seqtab_nochim, taxa_are_rows = FALSE), sample_data(samdf), tax_table(taxa), phy_tree(phy_tree))
  
  # store DNA sequences in refseq slot of phyloseq object and rename taxa to short taxa names
  dna <- Biostrings::DNAStringSet(taxa_names(ps))
  names(dna) <- taxa_names(ps)
  ps <- merge_phyloseq(ps, dna)
  taxa_names(ps) <- sprintf("feature_%04d", seq_len(ntaxa(ps)))
  
  return(list(ps = ps, taxa_order = taxa_order, samdf = samdf))
}

setup_tables <- function(directory, sample_sheet_path) {
  # Default Setup
  
  # import custom family colors
  colors <- read_excel(paste0(paste0(here(), '/1-data/Family_colors.xlsx')), sheet = 1)
  colors$Color <- paste0("#", colors$Color)
  colors <- colors %>% mutate(fOTU = paste(Kingdom, Phylum, Class, Order, Family, sep=";"))
  colors <- colors %>% mutate(fOTU = factor(fOTU, levels = rev(unique(colors$fOTU)), ordered = TRUE))
  
  # Create phyloseq object that stores:
  # otu_table <- table of read counts for each ASV
  # tax_table <- taxonomic assignment of ASVs
  # sample_data <- metadata for all experiments
  # phy_tree <- phylogenetic tree from data
  
  # setup tables to populate phyloseq object
  seqtab_nochim <- readRDS(paste0(directory,'seqtab_all.RDS')) # read in ASV read counts
  taxa <- read.table(paste0(directory,'feature_data.txt'), header = TRUE, sep = "\t") # read in ASV taxon info
  taxa <- taxa %>% mutate(fOTU = paste(Kingdom, Phylum, Class, Order, Family, sep=";")) %>% # add fOTU
    mutate(Taxon = mapply(generate_taxon, Kingdom, Phylum, Class, Order, Family, Genus, Species)) %>% # add concise taxonomy name to plot
    mutate(Family2 = ifelse(is.na(Family) | Family == "f__", Taxon, Family)) %>% # add Family2 name to plot
    left_join(colors %>% select(fOTU, Color), by = c("fOTU")) # add Family colors 
  taxa_order <- taxa %>% arrange(match(fOTU, colors$fOTU)) # arrange taxa based on fOTU order in colors
  rownames(taxa) <- taxa$Sequence # row names must match species.names
  taxa <- taxa %>% select(c("Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species", "fOTU", "Taxon", "Family2", "Color", "Feature"))
  taxa <- as.matrix(taxa) # taxa must be matrix
  
  phy_tree <- read_tree(paste0(directory,'dsvs_msa.tree')) # read in phylogenetic tree
  samdf <- read_excel(paste0(here(), sample_sheet_path), sheet = 1) # Read in sample metadata
  samdf <- as.data.frame(samdf) # convert to dataframe
  rownames(samdf) <- sub('sample_', '', samdf$Sample) # change row names to be the sequencing name, remove "sample_"
  samdf <- samdf[2:ncol(samdf)] # remove Sample column
  
  # create phyloseq object
  ps <- phyloseq(otu_table(seqtab_nochim, taxa_are_rows = FALSE), sample_data(samdf), tax_table(taxa), phy_tree(phy_tree))
  
  # store DNA sequences in refseq slot of phyloseq object and rename taxa to short taxa names
  dna <- Biostrings::DNAStringSet(taxa_names(ps))
  names(dna) <- taxa_names(ps)
  ps <- merge_phyloseq(ps, dna)
  taxa_names(ps) <- sprintf("feature_%04d", seq_len(ntaxa(ps)))
  
  return(list(ps = ps, taxa_order = taxa_order, samdf = samdf))
}

setup_tables2 <- function(directory, sample_sheet_path) {
  
  # import custom family colors
  colors <- read_excel(paste0(paste0(here(), '/1-data/Family_colors.xlsx')), sheet = 2)
  colors$Color <- paste0("#", colors$Color)
  colors <- colors %>% mutate(fOTU = paste(Kingdom, Phylum, Class, Order, Family, sep=";"))
  colors <- colors %>% mutate(fOTU = factor(fOTU, levels = rev(unique(colors$fOTU)), ordered = TRUE))
  
  seqtab_nochim <- read.table(paste0(directory,'dsvs.master.txt'), header = TRUE, row.names = 1, sep="\t", colClasses = rep("character", 6)) # read in ASV read counts
  taxa <- read.table(paste0(directory,'feature_data.txt'), header = TRUE, sep = "\t") # read in ASV taxon info
  taxa <- taxa %>% mutate(fOTU = paste(Kingdom, Phylum, Class, Order, Family, sep=";")) %>% # add fOTU
    mutate(Taxon = mapply(generate_taxon, Kingdom, Phylum, Class, Order, Family, Genus, Species)) %>% # add concise taxonomy name to plot
    mutate(Family2 = ifelse(is.na(Family) | Family == "f__", Taxon, Family)) %>% # add Family2 name to plot
    left_join(colors %>% select(fOTU, Color), by = c("fOTU")) # add Family colors 
  taxa_order <- taxa %>% arrange(match(fOTU, colors$fOTU)) # arrange taxa based on fOTU order in colors
  rownames(taxa) <- taxa$Feature # row names must match species.names
  taxa <- as.matrix(taxa) # taxa must be matrix
  
  seqtab_matrix <- as.matrix(seqtab_nochim)
  mode(seqtab_matrix) <- "numeric"
  
  samdf <- read_excel(paste0(here(), sample_sheet_path), sheet = 2) # Read in sample metadata
  samdf <- as.data.frame(samdf) # convert to dataframe
  rownames(samdf) <- sub('sample_', '', samdf$Sample) # change row names to be the sequencing name, remove "sample_"
  samdf <- samdf[2:ncol(samdf)] # remove Sample column
  
  # create phyloseq object
  ps <- phyloseq(otu_table(seqtab_matrix, taxa_are_rows = FALSE), sample_data(samdf), tax_table(taxa))
  
  return(list(ps = ps, taxa_order = taxa_order, samdf = samdf))
}

generate_taxon <- function(Kingdom, Phylum, Class, Order, Family, Genus, Species) {
  # Check for missing or placeholder values and create Taxon
  if (is.na(Genus) | gsub("g__", "", Genus) == "") {
    if (is.na(Family) | gsub("f__", "", Family) == "") {
      if (is.na(Order) | gsub("o__", "", Order) == "") {
        if (is.na(Class) | gsub("c__", "", Class) == "") {
          if (is.na(Phylum) | gsub("p__", "", Phylum) == "") {
            return(paste("k:", gsub("k__", "", Kingdom)))  # Use Kingdom if Phylum is missing
          } else {
            return(paste("p:", gsub("p__", "", Phylum)))  # Use Phylum if Class is missing
          }
        } else {
          return(paste("c:", gsub("c__", "", Class)))  # Use Class if Order and Family are missing
        }
      } else {
        return(paste("o:", gsub("o__", "", Order)))  # Use Order if Family is missing
      }
    } else {
      return(paste("f:", gsub("f__", "", Family)))  # Use Family if Genus is missing
    }
  } else {
    if (is.na(Species) | gsub("s__", "", Species) == "") {
      return(paste(gsub("g__", "", Genus), "sp."))  # Use Genus and "sp" if Species is missing
    } else {
      return(paste(gsub("g__", "", Genus), gsub("s__", "", Species)))  # Use Genus and Species
    }
  }
}

set_family_order <- function(df2plot, taxa_order) {
  df2plot <- df2plot %>% 
    arrange(match(fOTU, taxa_order$fOTU)) %>% # rearrange row order to fOTU order
    mutate(Family2 = factor(Family2, levels = unique(taxa_order$Family2))) %>% # set new Family2 order
    return(df2plot)
}

get_color_mapping <- function(df2plot){
  # Given a long form data frame, return a mapping of Color (HEX code) to Family2, sorted in Family2 order.
  family2_scale <- unique(df2plot[, c("Color", "Family2")])
  family2_scale$labels <- gsub("f__", "", family2_scale$Family2)
  
  # if any colors do not exist, print the missing family to the console.
  if (anyNA(family2_scale$Color)) { 
    indices <- which(is.na(family2_scale$Color))
    for (i in indices) {
      print(paste("Missing Family color: ", family2_scale$Family2[i]))
    }
  }
  names(family2_scale) <- c("values", "breaks", "labels")
  return(family2_scale)
}

get_evals <- function(pcoa_out){
  # function to get variance percentages
  evals <- pcoa_out$values[,1]
  var_exp <- 100 * evals/sum(evals)
  return(list("evals" = evals, "variance_exp" = var_exp))
}

theme_custom_comp <- function() {
  # Set default plotting method for composition in ggplot2
  theme(
    axis.ticks.y = element_blank(),
    axis.title.x = element_blank(),
    axis.text.x = element_blank(), 
    axis.ticks.x = element_blank(),
    panel.background = element_blank(),
    axis.text.y = element_text(margin = margin(r = 0.5)),
    legend.position = "none", # no legend
  )
}

theme_custom_text <- function() {
  # set all fontsizes to be 6 and black
  theme(
    legend.text = element_text(size = 6, color = "black"),
    legend.title = element_text(size = 6, color = "black"), 
    axis.text = element_text(size = 6, color = "black"),    
    axis.title = element_text(size = 7, color = "black"),  
    plot.title = element_text(size = 6, color = "black"),   
    strip.text = element_text(size = 6, color = "black"),
    plot.subtitle = element_text(size = 6, color = "black"),
    axis.ticks = element_line(color = "black", linewidth = 0.25),
    panel.grid.major = element_line(linewidth = 0.25)
  )
}

theme_custom_heatmap <- function() {
  # Set default plotting method for heatmaps in ggplot2
  theme(strip.text.y = element_blank(),
        axis.title.x = element_blank(),
        axis.title.y = element_blank(),
        axis.ticks.y = element_blank(),
        axis.text.x = element_text(),
        axis.ticks.x = element_blank())
}

red_if_small_discrete <- function(values) {
  # make text red if total reads is less than 10 K
  sapply(values, function(v) {
    v_num <- as.numeric(as.character(v))  # convert factor/char to number
    if (!is.na(v_num) && v_num < 10000) {
      paste0("<span style='color:red;'>", v, "</span>")
    } else {
      v
    }
  })
}

red_if_small_discrete_cap <- function(values) {
  # option when you want region and total reads
  sapply(values, function(v) {
  
    parts <- strsplit(as.character(v), "\\.")[[1]]
    if (length(parts) > 1) {
      v_num <- as.numeric(parts[1])  # get the part after the period
    } else {
      v_num <- NA
    }
    
    if (!is.na(v_num) && v_num < 10000) {
      paste0("<span style='color:red;'>", v, "</span>")
    } else {
      v
    }
  })
}

red_if_small_discrete_reads_only <- function(values) {
  # option when you want region and total reads
  sapply(values, function(v) {
    #v_num <- as.numeric(as.character(v))  # convert factor/char to number
    
    parts <- strsplit(as.character(v), "\\.")[[1]]
    if (length(parts) > 1) {
      v_num <- as.numeric(parts[1])  # get the part after the period
    } else {
      v_num <- NA
    }
    
    if (!is.na(v_num) && v_num < 10000) {
      paste0("<span style='color:red;'>", v_num, "</span>")
    } else {
      v_num
    }
  })
}

red_if_small_discrete_mgx <- function(values) {
  # option when you want region and total reads
  sapply(values, function(v) {
    
    parts <- strsplit(as.character(v), "\\.")[[1]]
    if (length(parts) > 1) {
      v_num <- as.numeric(parts[1])  # get the part after the period
    } else {
      v_num <- NA
    }
    
    if (!is.na(v_num) && v_num < 700000) {
      paste0("<span style='color:red;'>", v, "</span>")
    } else {
      v
    }
  })
}

calculate_rolling_centroids <- function(data, window_size = 3, sample_origin) {
  
  # Determine which day variable to use and diet variable
  if(sample_origin == "Cap") {
    day_var <- "Running_ingestion_day"
    diet_var <- "Diet_ingestion"
  } else {
    day_var <- "Running_collection_day"
    diet_var <- "Diet_collection"
  }
  
  data %>%
    mutate(day_value = as.numeric(.data[[day_var]])) %>%  # Use .data[[]] for proper column reference
    arrange(Subject_no, d_metric, day_value) %>%
    group_by(Subject_no, d_metric) %>%
    do({
      df <- .
      
      # Get unique days
      unique_days <- sort(unique(df$day_value))
      n_days <- length(unique_days)
      
      if (n_days < window_size) {
        data.frame()
      } else {
        rolling_data <- map_dfr(1:(n_days - window_size + 1), function(i) {
          # Get the day range for this window
          day_range <- unique_days[i:(i + window_size - 1)]
          window_data <- df %>% filter(day_value >= min(day_range) & day_value <= max(day_range))
          
          # Get diet from the lowest day in the window
          diet_value <- window_data %>% 
            filter(day_value == min(day_value)) %>% 
            pull(!!sym(diet_var)) %>% 
            unique() %>% 
            first()
          
          result <- data.frame(
            window_start = min(day_range),
            window_end = max(day_range),
            centroid_x = mean(window_data$Axis.1, na.rm = TRUE),
            centroid_y = mean(window_data$Axis.2, na.rm = TRUE),
            Subject_no = unique(window_data$Subject_no),
            d_metric = unique(window_data$d_metric),
            sample_origin = sample_origin
          )
          
          # Add the appropriate diet column
          result[[diet_var]] <- diet_value
          result
        })
        rolling_data
      }
    }) %>%
    ungroup()
}

# barplot_connect_ASV <- function(df_subj, color_scale, flow_alpha = 1, sample_origin) {
#   
#   # Prepare the data - aggregate and normalize by timepoint at Feature level
#   df_bars <- df_subj %>%
#     group_by(timeline, Feature, Family2) %>%
#     summarise(Abundance = sum(Abundance), .groups = "drop") %>%
#     group_by(timeline) %>%
#     mutate(
#       rel_abundance = Abundance / sum(Abundance)
#     ) %>%
#     ungroup() %>%
#     arrange(timeline, desc(Family2), Feature) %>%
#     group_by(timeline) %>%
#     mutate(
#       ymax = cumsum(rel_abundance),
#       ymin = ymax - rel_abundance
#     ) %>%
#     ungroup()
#   
#   timepoints <- sort(unique(df_bars$timeline))
#   
#   # For each Feature, create interpolated data between timepoints where it exists
#   ribbon_data <- list()
#   
#   for (feature in unique(df_bars$Feature)) {
#     feature_data <- df_bars %>% 
#       filter(Feature == feature) %>%
#       arrange(timeline)
#     
#     # Only process if feature appears at multiple timepoints
#     if (nrow(feature_data) > 1) {
#       # Create fine interpolation between consecutive points where feature exists
#       expanded_data <- data.frame()
#       
#       for (i in 1:(nrow(feature_data) - 1)) {
#         t_start <- feature_data$timeline[i]
#         t_end <- feature_data$timeline[i + 1]
#         
#         # Check if these are consecutive timepoints or if there's a gap
#         # Only interpolate if both values are finite
#         if (is.finite(t_start) && is.finite(t_end) && t_start < t_end) {
#           # Create interpolation points
#           t_seq <- seq(t_start, t_end, length.out = 100)
#           
#           ymin_seq <- approx(x = c(t_start, t_end),
#                              y = c(feature_data$ymin[i], feature_data$ymin[i + 1]),
#                              xout = t_seq)$y
#           
#           ymax_seq <- approx(x = c(t_start, t_end),
#                              y = c(feature_data$ymax[i], feature_data$ymax[i + 1]),
#                              xout = t_seq)$y
#           
#           segment_data <- data.frame(
#             timeline = t_seq,
#             ymin = ymin_seq,
#             ymax = ymax_seq,
#             Feature = feature,
#             Family2 = feature_data$Family2[i]
#           )
#           
#           expanded_data <- rbind(expanded_data, segment_data)
#         }
#       }
#       
#       if (nrow(expanded_data) > 0) {
#         ribbon_data[[feature]] <- expanded_data
#       }
#     }
#   }
#   
#   all_ribbons <- bind_rows(ribbon_data)
#   
#   # Create diet annotation data (moved higher)
#   diet_data <- data.frame(
#     xmin = c(0, 15, 22, 30, 33),
#     xmax = c(15, 22, 30, 33, max(timepoints)),
#     diet = c("Regular", "Keto", "Regular", "Fasting", "Regular"),
#     color = c("#B3B3B3", "blue", "#B3B3B3", "red", "#B3B3B3")
#   )
#   # Every 2 days for x-axis
#   day_breaks <- seq(0, max(timepoints), by = 2)
#   
#   # Create the plot
#   g <- ggplot() +
#     # Use geom_ribbon for smooth rendering
#     geom_ribbon(
#       data = all_ribbons,
#       aes(x = timeline, ymin = ymin, ymax = ymax, fill = Family2, group = Feature),
#       alpha = flow_alpha,
#       color = "black",
#       linewidth = 0.05
#     ) +
#     # Add box around main plot area (0-1, 0-max(timepoints))
#     geom_rect(
#       aes(xmin = 0, xmax = max(timepoints), ymin = 0, ymax = 1),
#       fill = NA,
#       color = "black",
#       linewidth = 0.1
#     ) +
#     # Add sampling day points between diet and ribbons
#     geom_point(
#       data = data.frame(x = timepoints, y = 1.02),
#       aes(x = x, y = y),
#       size = 0.5,
#       color = "black",
#       shape = 16
#     ) +
#     # Add diet rectangles (higher up)
#     geom_rect(
#       data = diet_data,
#       aes(xmin = xmin, xmax = xmax, ymin = 1.04, ymax = 1.08),
#       fill = diet_data$color,
#       alpha = 0.25,
#       color = "black",
#       linewidth = 0.1
#     ) +
#     # Add white diet labels
#     geom_text(
#       data = diet_data,
#       aes(x = (xmin + xmax) / 2, y = 1.06, label = diet),
#       size = 2,
#       color = "black"
#     ) +
#     scale_y_continuous(
#       "Relative Abundance", 
#       breaks = c(0.00, 0.25, 0.50, 0.75, 1.00),
#       limits = c(0, 1.10),
#       expand = c(0, 0)
#     ) +
#     scale_x_continuous(
#       "Days",
#       breaks = day_breaks,
#       expand = c(0.01, 0)
#     ) +
#     scale_fill_manual(
#       values = color_scale$values, 
#       breaks = color_scale$breaks, 
#       labels = color_scale$labels
#     ) +
#     theme_custom_comp() +
#     theme(
#       panel.spacing = unit(0.5, "lines"),
#       legend.position = "none",
#       axis.text.x = element_text(),
#       axis.title.x = element_text()
#     ) +
#     theme_custom_text()
#   
#   return(g)
# }
# 
# barplot_connect_family <- function(df_subj, color_scale, flow_alpha = 1) {
#   
#   # Prepare the data - aggregate and normalize by timepoint at Family level
#   df_bars <- df_subj %>%
#     group_by(timeline, Family2) %>%
#     summarise(Abundance = sum(Abundance), .groups = "drop") %>%
#     group_by(timeline) %>%
#     mutate(
#       rel_abundance = Abundance / sum(Abundance)
#     ) %>%
#     ungroup() %>%
#     arrange(timeline, desc(Family2)) %>%
#     group_by(timeline) %>%
#     mutate(
#       ymax = cumsum(rel_abundance),
#       ymin = ymax - rel_abundance
#     ) %>%
#     ungroup()
#   
#   timepoints <- sort(unique(df_bars$timeline))
#   
#   # For each Family, create interpolated data between timepoints where it exists
#   ribbon_data <- list()
#   
#   for (family in unique(df_bars$Family2)) {
#     family_data <- df_bars %>% 
#       filter(Family2 == family) %>%
#       arrange(timeline)
#     
#     # Only process if family appears at multiple timepoints
#     if (nrow(family_data) > 1) {
#       # Create fine interpolation between consecutive points where family exists
#       expanded_data <- data.frame()
#       
#       for (i in 1:(nrow(family_data) - 1)) {
#         t_start <- family_data$timeline[i]
#         t_end <- family_data$timeline[i + 1]
#         
#         # Check if these are consecutive timepoints or if there's a gap
#         # Only interpolate if both values are finite
#         if (is.finite(t_start) && is.finite(t_end) && t_start < t_end) {
#           # Create interpolation points
#           t_seq <- seq(t_start, t_end, length.out = 100)
#           
#           ymin_seq <- approx(x = c(t_start, t_end),
#                              y = c(family_data$ymin[i], family_data$ymin[i + 1]),
#                              xout = t_seq)$y
#           
#           ymax_seq <- approx(x = c(t_start, t_end),
#                              y = c(family_data$ymax[i], family_data$ymax[i + 1]),
#                              xout = t_seq)$y
#           
#           segment_data <- data.frame(
#             timeline = t_seq,
#             ymin = ymin_seq,
#             ymax = ymax_seq,
#             Family2 = family
#           )
#           
#           expanded_data <- rbind(expanded_data, segment_data)
#         }
#       }
#       
#       if (nrow(expanded_data) > 0) {
#         ribbon_data[[family]] <- expanded_data
#       }
#     }
#   }
#   
#   all_ribbons <- bind_rows(ribbon_data)
#   
#   # Create diet annotation data (moved higher)
#   diet_data <- data.frame(
#     xmin = c(0, 15, 22, 30, 33),
#     xmax = c(15, 22, 30, 33, max(timepoints)),
#     diet = c("Regular", "Keto", "Regular", "Fasting", "Regular"),
#     color = c("#B3B3B3", "blue", "#B3B3B3", "red", "#B3B3B3")
#   )
#   
#   # Every 2 days for x-axis
#   day_breaks <- seq(0, max(timepoints), by = 2)
#   
#   # Create the plot
#   g <- ggplot() +
#     # Use geom_ribbon for smooth rendering
#     geom_ribbon(
#       data = all_ribbons,
#       aes(x = timeline, ymin = ymin, ymax = ymax, fill = Family2, group = Family2),
#       alpha = flow_alpha,
#       color = "black",
#       linewidth = 0.1
#     ) +
#     # Add box around main plot area (0-1, 0-max(timepoints))
#     geom_rect(
#       aes(xmin = 0, xmax = max(timepoints), ymin = 0, ymax = 1),
#       fill = NA,
#       color = "black",
#       linewidth = 0.1
#     ) +
#     # Add sampling day points between diet and ribbons
#     geom_point(
#       data = data.frame(x = timepoints, y = 1.02),
#       aes(x = x, y = y),
#       size = 0.5,
#       color = "black",
#       shape = 16
#     ) +
#     # Add diet rectangles (higher up)
#     geom_rect(
#       data = diet_data,
#       aes(xmin = xmin, xmax = xmax, ymin = 1.04, ymax = 1.08),
#       fill = diet_data$color,
#       color = "black",
#       alpha = 0.25,
#       linewidth = 0.1
#     ) +
#     # Add white diet labels
#     geom_text(
#       data = diet_data,
#       aes(x = (xmin + xmax) / 2, y = 1.06, label = diet),
#       size = 2,
#       color = "black"
#     ) +
#     scale_y_continuous(
#       "Relative Abundance", 
#       breaks = c(0.00, 0.25, 0.50, 0.75, 1.00),
#       limits = c(0, 1.10),
#       expand = c(0, 0)
#     ) +
#     scale_x_continuous(
#       "Days",
#       breaks = day_breaks,
#       expand = c(0.01, 0)
#     ) +
#     scale_fill_manual(
#       values = color_scale$values, 
#       breaks = color_scale$breaks, 
#       labels = color_scale$labels
#     ) +
#     theme_custom_comp() +
#     theme(
#       panel.spacing = unit(0.5, "lines"),
#       legend.position = "none",
#       axis.text.x = element_text(),
#       axis.title.x = element_text()
#     ) +
#     theme_custom_text()
#   
#   return(g)
# }

barplot_connect_ASV <- function(df_subj, color_scale, flow_alpha = 1, sample_origin) {
  
  # Select appropriate timeline column based on sample_origin
  timeline_col <- if (sample_origin == "Stool") {
    "Collection_timeline"
  } else if (sample_origin == "Cap") {
    "Ingestion_timeline"
  } else {
    "timeline"  # fallback
  }
  
  # Rename to generic 'timeline' for processing
  df_subj <- df_subj %>%
    rename(timeline = !!sym(timeline_col)) %>%
    mutate(timeline = as.numeric(as.character(timeline)))
  
  # Prepare the data - aggregate and normalize by timepoint at Feature level
  df_bars <- df_subj %>%
    group_by(timeline, Feature, Family2) %>%
    summarise(Abundance = sum(Abundance), .groups = "drop") %>%
    group_by(timeline) %>%
    mutate(
      rel_abundance = Abundance / sum(Abundance)
    ) %>%
    ungroup() %>%
    arrange(timeline, desc(Family2), Feature) %>%
    group_by(timeline) %>%
    mutate(
      ymax = cumsum(rel_abundance),
      ymin = ymax - rel_abundance
    ) %>%
    ungroup()
  
  timepoints <- sort(unique(df_bars$timeline))
  
  # For each Feature, create interpolated data between timepoints where it exists
  ribbon_data <- list()
  
  for (feature in unique(df_bars$Feature)) {
    feature_data <- df_bars %>% 
      filter(Feature == feature) %>%
      arrange(timeline)
    
    # Only process if feature appears at multiple timepoints
    if (nrow(feature_data) > 1) {
      # Create fine interpolation between consecutive points where feature exists
      expanded_data <- data.frame()
      
      for (i in 1:(nrow(feature_data) - 1)) {
        t_start <- feature_data$timeline[i]
        t_end <- feature_data$timeline[i + 1]
        
        # Check if these are consecutive timepoints or if there's a gap
        # Only interpolate if both values are finite
        if (is.finite(t_start) && is.finite(t_end) && t_start < t_end) {
          # Create interpolation points
          t_seq <- seq(t_start, t_end, length.out = 100)
          
          ymin_seq <- approx(x = c(t_start, t_end),
                             y = c(feature_data$ymin[i], feature_data$ymin[i + 1]),
                             xout = t_seq)$y
          
          ymax_seq <- approx(x = c(t_start, t_end),
                             y = c(feature_data$ymax[i], feature_data$ymax[i + 1]),
                             xout = t_seq)$y
          
          segment_data <- data.frame(
            timeline = t_seq,
            ymin = ymin_seq,
            ymax = ymax_seq,
            Feature = feature,
            Family2 = feature_data$Family2[i]
          )
          
          expanded_data <- rbind(expanded_data, segment_data)
        }
      }
      
      if (nrow(expanded_data) > 0) {
        ribbon_data[[feature]] <- expanded_data
      }
    }
  }
  
  all_ribbons <- bind_rows(ribbon_data)
  
  # Create diet annotation data (moved higher)
  diet_data <- data.frame(
    xmin = c(0, 15, 22, 30, 33),
    xmax = c(15, 22, 30, 33, max(timepoints)),
    diet = c("Regular", "Keto", "Regular", "Fasting", "Regular"),
    color = c("#B3B3B3", "blue", "#B3B3B3", "red", "#B3B3B3")
  )
  # Every 2 days for x-axis
  day_breaks <- seq(0, max(timepoints), by = 2)
  
  # Create the plot
  g <- ggplot() +
    # Use geom_ribbon for smooth rendering
    geom_ribbon(
      data = all_ribbons,
      aes(x = timeline, ymin = ymin, ymax = ymax, fill = Family2, group = Feature),
      alpha = flow_alpha,
      color = "black",
      linewidth = 0.05
    ) +
    # Add box around main plot area (0-1, 0-max(timepoints))
    geom_rect(
      aes(xmin = 0, xmax = max(timepoints), ymin = 0, ymax = 1),
      fill = NA,
      color = "black",
      linewidth = 0.1
    ) +
    # Add sampling day points between diet and ribbons
    geom_point(
      data = data.frame(x = timepoints, y = 1.02),
      aes(x = x, y = y),
      size = 0.5,
      color = "black",
      shape = 16
    ) +
    # Add diet rectangles (higher up)
    geom_rect(
      data = diet_data,
      aes(xmin = xmin, xmax = xmax, ymin = 1.04, ymax = 1.08),
      fill = diet_data$color,
      alpha = 0.25,
      color = "black",
      linewidth = 0.1
    ) +
    # Add white diet labels
    geom_text(
      data = diet_data,
      aes(x = (xmin + xmax) / 2, y = 1.06, label = diet),
      size = 2,
      color = "black"
    ) +
    scale_y_continuous(
      "Relative Abundance", 
      breaks = c(0.00, 0.25, 0.50, 0.75, 1.00),
      limits = c(0, 1.10),
      expand = c(0, 0)
    ) +
    scale_x_continuous(
      "Days",
      breaks = day_breaks,
      expand = c(0.01, 0)
    ) +
    scale_fill_manual(
      values = color_scale$values, 
      breaks = color_scale$breaks, 
      labels = color_scale$labels
    ) +
    theme_custom_comp() +
    theme(
      panel.spacing = unit(0.5, "lines"),
      legend.position = "none",
      axis.text.x = element_text(),
      axis.title.x = element_text()
    ) +
    theme_custom_text()
  
  return(g)
}

barplot_connect_family <- function(df_subj, color_scale, flow_alpha = 1, sample_origin) {
  
  # Select appropriate timeline column based on sample_origin
  timeline_col <- if (sample_origin == "Stool") {
    "Collection_timeline"
  } else if (sample_origin == "Cap") {
    "Ingestion_timeline"
  } else {
    "timeline"  # fallback
  }
  
  # Rename to generic 'timeline' for processing
  df_subj <- df_subj %>%
    rename(timeline = !!sym(timeline_col)) %>%
    mutate(timeline = as.numeric(as.character(timeline)))
  
  # Prepare the data - aggregate and normalize by timepoint at Family level
  df_bars <- df_subj %>%
    group_by(timeline, Family2) %>%
    summarise(Abundance = sum(Abundance), .groups = "drop") %>%
    group_by(timeline) %>%
    mutate(
      rel_abundance = Abundance / sum(Abundance)
    ) %>%
    ungroup() %>%
    arrange(timeline, desc(Family2)) %>%
    group_by(timeline) %>%
    mutate(
      ymax = cumsum(rel_abundance),
      ymin = ymax - rel_abundance
    ) %>%
    ungroup()
  
  timepoints <- sort(unique(df_bars$timeline))
  
  # For each Family, create interpolated data between timepoints where it exists
  ribbon_data <- list()
  
  for (family in unique(df_bars$Family2)) {
    family_data <- df_bars %>% 
      filter(Family2 == family) %>%
      arrange(timeline)
    
    # Only process if family appears at multiple timepoints
    if (nrow(family_data) > 1) {
      # Create fine interpolation between consecutive points where family exists
      expanded_data <- data.frame()
      
      for (i in 1:(nrow(family_data) - 1)) {
        t_start <- family_data$timeline[i]
        t_end <- family_data$timeline[i + 1]
        
        # Check if these are consecutive timepoints or if there's a gap
        # Only interpolate if both values are finite
        if (is.finite(t_start) && is.finite(t_end) && t_start < t_end) {
          # Create interpolation points
          t_seq <- seq(t_start, t_end, length.out = 100)
          
          ymin_seq <- approx(x = c(t_start, t_end),
                             y = c(family_data$ymin[i], family_data$ymin[i + 1]),
                             xout = t_seq)$y
          
          ymax_seq <- approx(x = c(t_start, t_end),
                             y = c(family_data$ymax[i], family_data$ymax[i + 1]),
                             xout = t_seq)$y
          
          segment_data <- data.frame(
            timeline = t_seq,
            ymin = ymin_seq,
            ymax = ymax_seq,
            Family2 = family
          )
          
          expanded_data <- rbind(expanded_data, segment_data)
        }
      }
      
      if (nrow(expanded_data) > 0) {
        ribbon_data[[family]] <- expanded_data
      }
    }
  }
  
  all_ribbons <- bind_rows(ribbon_data)
  
  # Create diet annotation data (moved higher)
  diet_data <- data.frame(
    xmin = c(0, 15, 22, 30, 33),
    xmax = c(15, 22, 30, 33, max(timepoints)),
    diet = c("Regular", "Keto", "Regular", "Fasting", "Regular"),
    color = c("#B3B3B3", "blue", "#B3B3B3", "red", "#B3B3B3")
  )
  
  # Every 2 days for x-axis
  day_breaks <- seq(0, max(timepoints), by = 2)
  
  # Create the plot
  g <- ggplot() +
    # Use geom_ribbon for smooth rendering
    geom_ribbon(
      data = all_ribbons,
      aes(x = timeline, ymin = ymin, ymax = ymax, fill = Family2, group = Family2),
      alpha = flow_alpha,
      color = "black",
      linewidth = 0.1
    ) +
    # Add box around main plot area (0-1, 0-max(timepoints))
    geom_rect(
      aes(xmin = 0, xmax = max(timepoints), ymin = 0, ymax = 1),
      fill = NA,
      color = "black",
      linewidth = 0.1
    ) +
    # Add sampling day points between diet and ribbons
    geom_point(
      data = data.frame(x = timepoints, y = 1.02),
      aes(x = x, y = y),
      size = 0.5,
      color = "black",
      shape = 16
    ) +
    # Add diet rectangles (higher up)
    geom_rect(
      data = diet_data,
      aes(xmin = xmin, xmax = xmax, ymin = 1.04, ymax = 1.08),
      fill = diet_data$color,
      color = "black",
      alpha = 0.25,
      linewidth = 0.1
    ) +
    # Add white diet labels
    geom_text(
      data = diet_data,
      aes(x = (xmin + xmax) / 2, y = 1.06, label = diet),
      size = 2,
      color = "black"
    ) +
    scale_y_continuous(
      "Relative Abundance", 
      breaks = c(0.00, 0.25, 0.50, 0.75, 1.00),
      limits = c(0, 1.10),
      expand = c(0, 0)
    ) +
    scale_x_continuous(
      "Days",
      breaks = day_breaks,
      expand = c(0.01, 0)
    ) +
    scale_fill_manual(
      values = color_scale$values, 
      breaks = color_scale$breaks, 
      labels = color_scale$labels
    ) +
    theme_custom_comp() +
    theme(
      panel.spacing = unit(0.5, "lines"),
      legend.position = "none",
      axis.text.x = element_text(),
      axis.title.x = element_text()
    ) +
    theme_custom_text()
  
  return(g)
}
