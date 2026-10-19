"""Classify every lexicon ingredient: is a result expected in trnL / 12SV5 sequencing?
Status: Yes / Uncertain / No.  'No' = nothing comparable is expected (no marker, DNA removed by processing, or no single taxon to compare)."""
G = []  # (status, category, reason template, [ingredients])
def add(status, cat, reason, names): G.append((status, cat, reason, names))

add("No","No marker in pipeline",
    "Fungus (or yeast). The pipeline's two markers, trnL (land-plant chloroplast) and 12SV5 (vertebrate mitochondrial 12S), do not target fungi, so no result is expected.",
    ["chanterelle","enoki","mushroom","oyster mushroom","shiitake","truffle","wood ear","nutritional yeast"])
add("No","No marker in pipeline",
    "Invertebrate (crustacean/mollusc). 12SV5 is vertebrate-specific and trnL is plant-specific, so no result is expected.",
    ["crab","shrimp","octopus","scallop","squid","shellfish"])
add("No","No marker in pipeline",
    "Bee product. 12SV5 is vertebrate-specific; any plant DNA in honey is pollen from unknown flowers, not a traceable ingredient.",
    ["honey"])
add("No","Distilled",
    "Distilled alcohol. Distillation removes DNA, so the base plant is not expected to appear.",
    ["amaro","bourbon","herbal liqueur","limoncello","soju","spirits","whiskey"])
add("No","Refined / purified",
    "Refined sugar or syrup: purified sugar contains no intact plant DNA. (Beta/Saccharum DNA in the run comes from whole foods such as beet, not from sugar.)",
    ["sugar","agave","maple syrup"])
add("No","Refined / purified",
    "Refined oil, assumed (vegetable oil is generic): oil refining removes nearly all DNA. Soy/Brassica DNA in the run comes from whole soy and Brassica foods.",
    ["vegetable oil"])
add("No","Refined / purified",
    "Purified starch: starch isolation leaves little or no DNA.",
    ["tapioca"])
add("No","No food DNA",
    "Contains no food-derived DNA (artificial sweeteners/flavours, or a tablet/capsule of unknown content).",
    ["diet soda","supplement"])
add("No","Hydrolysed / isolated / fat",
    "Hydrolysed or isolated animal protein, or a milk fat: processing removes most cells and DNA. Cow/pig DNA in the run comes from meat and whole dairy, not from this.",
    ["collagen","gelatin","whey","butter"])
add("No","Hydrolysed / isolated / fat",
    "Isolated plant protein: isolation leaves little DNA.",
    ["pea protein"])
add("No","Unspecified taxon",
    "Log gives no usable taxon (for example '{n}'), so there is no single species or genus to compare with sequencing, even though some DNA may be detected.",
    ["unknown","fruit (unspecified)","mixed vegetables","nuts (unspecified)","trail mix","jam","fish","seafood (mixed)",
     "grain cereal","grain-free cereal","plant-based mince","vegan caesar dressing","protein powder"])

add("Uncertain","Processed: DNA reduced",
    "Fermented, filtered or heat-processed: DNA is reduced but may survive. Do not count a miss as a false negative.",
    ["almond milk","oat milk","soy milk","soy sauce","miso","soybean paste","hoisin sauce","soy meat","balsamic vinegar",
     "beer","wine","olive oil","imitation crab","coffee","tea"])
add("Uncertain","Trace amount",
    "Eaten in small quantity (spice, herb or flavouring): DNA may be below detection or swamped by main foods.",
    ["black pepper","cinnamon","cumin","curry spices","saffron","vanilla","bergamot","turmeric","anchovy","wasabi","thousand island dressing"])
add("Uncertain","Low DNA",
    "Egg white has almost no DNA and yolk little; detection is unreliable. Chicken DNA in the run also comes from chicken meat.",
    ["egg","quail egg"])
add("Uncertain","Composite product",
    "Packaged or blended product whose composition is not stated in the log (taken from memory of the label or a typical blend), so which species should appear is uncertain.",
    ["huel","ikea plant balls","impossible meat","vegan cheese","gluten-free flour"])
add("Uncertain","Partly unspecified",
    "Log names only a group (for example berries, stone fruit, beans) or an alga; a genus-level result is possible but the species is unspecified, and algae are not clearly covered by trnL.",
    ["berries (mixed)","stone fruit","beans (unspecified)","nori","seaweed"])

SPECIFIC = {
 "butter":"Milk fat: little cow cell material, so cow DNA is not expected from butter itself. Bos taurus in the run comes from milk, cheese and beef.",
 "vegetable oil":G[5][2],
 "coffee":"Roasted and brewed: roasting degrades DNA and the grounds are discarded. Also no Coffea or Rubiaceae genus in the plants output.",
 "tea":"Brewed: leaves are discarded and the liquid carries little DNA (tea leaves eaten whole would be different).",
 "wine":"Filtered fermented drink: little DNA, but not zero.","beer":"Filtered fermented drink: little DNA, but not zero.",
 "olive oil":"Pressed oil: refined oil has little DNA, extra-virgin may retain a trace.",
 "imitation crab":"Surimi: washed fish mince (Alaska pollock) with starch; some fish DNA may survive.",
 "wasabi":"Usually horseradish-based paste in practice, so the species may not match; eaten in small amounts.",
 "anchovy":"Often a minor Caesar-dressing ingredient: small amount.",
 "soy sauce":"Fermented sauce: low DNA, and soy/wheat DNA also comes from other foods.",
 "miso":"Fermented paste: DNA reduced; soy also comes from tofu and other foods.",
 "soybean paste":"Fermented paste: DNA reduced.","hoisin sauce":"Fermented sauce, small amount: DNA reduced.",
 "soy meat":"Textured, defatted soy protein: extrusion and defatting reduce DNA.",
 "soy milk":"Filtered soy slurry: DNA reduced but probably present.","almond milk":"Filtered nut slurry: DNA reduced.","oat milk":"Enzyme-treated, filtered: DNA reduced.",
 "balsamic vinegar":"Acidic, filtered: DNA degraded.",
 "nori":"Red alga (Pyropia): not clearly amplified by trnL (unverified).","seaweed":"Alga: not clearly amplified by trnL (unverified); species assumed.",
 "berries (mixed)":"Mixed berries: could be Rubus, Fragaria or Vaccinium; genus-level result possible, species unspecified.",
 "stone fruit":"Prunus spp.: genus-level result possible, species unspecified.",
 "beans (unspecified)":"Bean type not stated (Phaseolus assumed); genus-level result possible only if the assumption is right.",
 "egg":"Egg white has almost no DNA and yolk little; detection is unreliable. Chicken DNA in the run also comes from chicken meat.",
 "quail egg":"Egg DNA is low and unreliable.",
 "curry spices":"Spice blend (turmeric, coriander, cumin); small amounts and composition varies.",
 "thousand island dressing":"Small amount of dressing; recipe varies.",
 "pea protein":"Isolated protein: little DNA.","tapioca":"Purified starch: little or no DNA.",
 "diet soda":"Contains no food DNA.","supplement":"Tablet or capsule of unknown content; no food DNA assumed.",
 "agave":"Refined syrup: no intact plant DNA expected.","sugar":"Refined sugar: no intact plant DNA expected. (Beta DNA in the run comes from whole foods such as beet and chard, not from sugar.)",
 "maple syrup":"Boiled-down sap syrup: no intact plant DNA expected.",
 "honey":"Bee product; 12SV5 is vertebrate-specific. Any plant DNA is pollen from unknown flowers, not a traceable ingredient.",
}
YES_NOTES = {
 "cheese":"Cow-milk cheese (assumed): contains milk cells; cow DNA expected, but ripening may reduce it. Same Bos taurus signal as milk and yogurt.",
 "cream cheese":"Cow-milk product: cow DNA expected; shares its signal with other dairy.",
 "goat cheese":"Goat-milk cheese: Capra hircus DNA expected (only 1 ASV labelled Capra hircus in the meat output).",
 "feta":"Sheep/goat cheese (US feta may be cow): DNA expected; species uncertain.",
 "paneer":"Cow-milk cheese (assumed): cow DNA expected.",
 "yogurt":"Cow-milk product (assumed): cow DNA expected; shares its signal with other dairy.",
 "ice cream":"Cow-milk product: cow DNA expected; flavour ingredients add other signals.",
 "cream":"Cow-milk product: cow DNA expected; shares its signal with other dairy.",
 "cow milk":"Whole cow milk: contains cells; Bos taurus DNA expected (same signal as beef and other dairy).",
 "tofu":"Coagulated whole-soybean curd: DNA expected to survive, though reduced by processing.",
 "tofu skin":"Soy-milk film: DNA expected, reduced by processing.",
 "natto":"Whole fermented soybeans: DNA expected.",
 "kimchi":"Fermented whole vegetables: DNA expected; recipe varies, so which species appear is uncertain.",
 "cacao":"Chocolate/cocoa: roasted and processed, but the Theobroma genus has many ASVs in the run, so detection is plausible.",
 "granola":"Oat-based cereal: DNA expected; composition varies.",
 "raisin":"Dried grape: DNA expected.",
 "apple":"Whole fruit: DNA expected. May merge with pear (Maleae); no Malus label in the plants output.",
}
def classify(ing, species, marker, note):
    for st, cat, reason, names in G:
        if ing in names:
            r = SPECIFIC.get(ing) or reason.replace("{n}", ing)
            return st, cat, r
    if ing in YES_NOTES:
        return "Yes", "Whole or lightly processed food", YES_NOTES[ing]
    # informative
    kind = "animal (vertebrate) food, amplified by 12SV5" if marker.startswith("12SV5") else "plant food, amplified by trnL"
    extra = ""
    if note and note != "None":
        extra = f" Resolution/caveat: {note}."
    return "Yes", "Whole or lightly processed food", f"Whole or lightly processed {kind}; DNA expected to survive.{extra}"
