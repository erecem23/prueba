# Fortaleza de la economía familiar

Análisis exploratorio de hogares a partir de variables seleccionadas de la **Encuesta Permanente de Hogares (EPH), tercer trimestre de 2025**, del INDEC.

El proyecto está presentado como una **notebook reproducible** que integra explicación, código, tablas, gráficos y conclusiones.

## Preguntas

- ¿Cómo se distribuye el ingreso per cápita familiar (IPCF)?
- ¿Qué diferencias aparecen entre aglomerados urbanos?
- ¿Qué estrategias financieras utilizan los hogares que no logran sostenerse con ingresos laborales?
- ¿Qué relación existe entre el tamaño del hogar y el IPCF?

## Estructura

```text
.
├── fortaleza_economia_familiar.ipynb
├── requirements.txt
└── README.md
```

La notebook intenta cargar una copia local del CSV si existe. Si no, descarga la planilla original compartida en Google Drive y procesa automáticamente la hoja `Datos`.

## Variables

- `AGLOMERADO`: código del aglomerado urbano.
- `IX_TOT`: cantidad de integrantes del hogar.
- `IPCF`: ingreso per cápita familiar.
- `V1`: vive de lo que gana en el trabajo.
- `V13`: uso de ahorros.
- `V15`: solicitud de préstamos bancarios/financieros.

En `V1`, `V13` y `V15`, `1 = Sí`, `2 = No` y `9 = NS/NR`; los códigos 9 se tratan como datos faltantes.

## Resultados principales

La muestra contiene 15.860 hogares. El IPCF presenta una marcada asimetría positiva y una dispersión elevada. Entre los hogares que declaran no poder vivir exclusivamente de sus ingresos laborales, el uso de ahorros aparece con mayor frecuencia que la solicitud de préstamos. El tamaño del hogar se relaciona negativamente con el IPCF, aunque una regresión lineal simple explica una proporción pequeña de su variabilidad.

## Nota metodológica

La base utilizada para este proyecto contiene una selección de variables y **no incluye `PONDERA`**. En consecuencia, los resultados son descriptivos de la muestra disponible y no deben interpretarse como estimaciones poblacionales ponderadas para el conjunto de hogares argentinos.

## Fuente

Instituto Nacional de Estadística y Censos (INDEC), Encuesta Permanente de Hogares, tercer trimestre de 2025.

- https://www.indec.gob.ar/indec/web/Institucional-Indec-BasesDeDatos
- https://www.indec.gob.ar/ftp/cuadros/menusuperior/eph/EPH_registro_3T2025.pdf

## Autoría

**Versión notebook:** Chris Moreno.

Adaptación de un trabajo grupal realizado para Análisis de Datos I, Licenciatura en Análisis y Gestión de Datos, Universidad Nacional de San Luis.

Trabajo original: Rocío Cacciamano, Federico Granero, Chris Moreno, Julián Reinoso y Jeremías Blejman.
