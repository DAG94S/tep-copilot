# Extrae las simulaciones 1..20 de cada falla de los .RData de ENTRENAMIENTO de Rieth et al. (2017)
# a binarios planos (double little-endian, orden: [columna][muestra] por simulacion) en data/raw/rieth/extraido/.
# Solo base R. Uso: /usr/bin/time -v Rscript scripts/extraer_rieth.R
dir <- "data/raw/rieth"
out <- file.path(dir, "extraido")
dir.create(out, showWarnings = FALSE, recursive = TRUE)
cols <- c(paste0("xmeas_", 1:41), paste0("xmv_", 1:11))

volcar <- function(df, falla, nombre) {
  sub <- df[df$faultNumber == falla & df$simulationRun <= 20, ]
  sub <- sub[order(sub$simulationRun, sub$sample), ]
  stopifnot(nrow(sub) == 20 * 500)
  m <- as.matrix(sub[, cols])               # (10000, 52), filas = corrida-major, muestra
  con <- file(file.path(out, nombre), "wb")
  writeBin(as.vector(t(m)), con, size = 8)  # fila a fila: 52 valores por muestra
  close(con)
}

for (arch in c("TEP_FaultFree_Training.RData", "TEP_Faulty_Training.RData")) {
  nm <- load(file.path(dir, arch))
  df <- get(nm[1]); rm(list = nm); gc()
  cat(arch, dim(df), "\n")
  if (grepl("FaultFree", arch)) {
    volcar(df, 0, "faultfree_train.bin")
  } else {
    for (f in 1:20)  # Rieth solo trae las fallas 1..20 (no la 21)
      volcar(df, f, sprintf("faulty_train_f%02d.bin", f))
  }
  rm(df); gc()
}
