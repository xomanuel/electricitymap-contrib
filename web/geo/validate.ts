import {
  area,
  bbox,
  bboxPolygon,
  convex,
  dissolve,
  Feature,
  featureCollection,
  featureEach,
  getGeom,
  intersect,
  Polygon,
} from '@turf/turf';

import { getConfig } from '../scripts/generateZonesConfig.js';
import { GeoConfig, WorldFeatureCollection } from './types.js';
import { getHoles, getPolygons, log, writeJSON } from './utilities.js';

// TODO: Improve this function so each check returns error messages,
// so we can show all errors instead of taking them one at a time.
function validateGeometry(fc: WorldFeatureCollection, config: GeoConfig) {
  console.info('Validating geometries...');
  zeroNullGeometries(fc);
  containsRequiredProperties(fc);
  zeroComplexPolygons(fc, config);
  zeroNeighboringIds(fc);
  zeroGaps(fc, config);
  zeroOverlaps(fc, config);
  matchesZonesConfig(fc);
}

function zeroNullGeometries(fc: WorldFeatureCollection) {
  const nullGeometries = fc.features
    .filter((ft) => getGeom(ft).coordinates.length === 0)
    .map((ft) => ft.properties.zoneName);
  if (nullGeometries.length > 0) {
    for (const zoneName of nullGeometries) {
      log(`${zoneName} has null geometry`);
    }
    throw new Error('Feature(s) contains null geometry');
  }
}

function containsRequiredProperties(fc: WorldFeatureCollection) {
  const indexes = getPolygons(fc)
    .features.map(({ properties }, index) =>
      properties?.zoneName || properties?.countryKey ? null : index
    )
    .filter(Boolean);

  if (indexes.length > 0) {
    for (const x of indexes) {
      log(`feature (idx ${x}) missing properties`);
    }
    throw new Error('Feature(s) are missing properties');
  }
}

function zeroComplexPolygons(
  fc: WorldFeatureCollection,
  { MAX_CONVEX_DEVIATION }: GeoConfig
) {
  // https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.73.1045&rep=rep1&type=pdf
  // calculate deviation from the convex hull and returns array of polygons with high complexity

  const zoneNames = getPolygons(fc)
    .features.map((ft) => {
      try {
        const convexFeature = convex(ft);
        if (convexFeature === null) {
          throw new Error("Can't calculate convex hull");
        }
        const deviation = (area(convexFeature) - area(ft)) / area(convexFeature);
        return { deviation, zoneName: ft.properties?.zoneName };
      } catch (error) {
        // assumes the feature is complex
        log(`${ft.properties?.zoneName} cannot calculate complexity`);
        console.error(error);
        return { deviation: Number.MAX_SAFE_INTEGER, zoneName: ft.properties?.zoneName };
      }
    })
    .filter((x) => x.deviation > MAX_CONVEX_DEVIATION)
    .map((x) => x.zoneName);

  if (zoneNames.length > 0) {
    for (const x of zoneNames) {
      log(`${x} is too complex`);
    }
    throw new Error('Feature(s) too complex');
  }
}

function matchesZonesConfig(fc: WorldFeatureCollection) {
  const config = getConfig();

  const missingZones: string[] = [];
  featureEach(fc, (ft) => {
    if (!(ft.properties?.zoneName in config.zones)) {
      missingZones.push(ft.properties?.zoneName);
    }
  });
  if (missingZones.length > 0) {
    for (const x of missingZones) {
      log(`${x} not in zones/*.yaml`);
    }
    throw new Error('Zonename not in zones/*.yaml');
  }
}

function zeroGaps(
  fc: WorldFeatureCollection,
  { ERROR_PATH, MIN_AREA_HOLES, SLIVER_RATIO }: GeoConfig
) {
  const dissolved = getPolygons(dissolve(getPolygons(fc)));
  const holes = getHoles(dissolved, MIN_AREA_HOLES, SLIVER_RATIO);

  if (holes.features.length > 0) {
    writeJSON(`${ERROR_PATH}/gaps.geojson`, holes);
    for (const _ of holes.features) {
      log(`Found gap, see gaps.geojson`);
    }
    throw new Error(
      'Contains gaps - please upload the file to QGIS or similar to inspect and remove the gaps'
    );
  }
}

function zeroNeighboringIds(fc: WorldFeatureCollection) {
  // Throws error if multiple polygons have the same zoneName and are right next to each other,
  // in that case they should be merged as one polygon
  const groupedByZoneNames = getPolygons(fc).features.reduce((accumulator, cval) => {
    const zoneName = cval.properties?.zoneName;
    if (accumulator[zoneName]) {
      accumulator[zoneName].push(cval);
    } else {
      accumulator[zoneName] = [cval];
    }
    return accumulator;
  }, {} as { [key: string]: Feature<Polygon>[] });

  // dissolve each group, if length decreases, it means that they are superfluous neigbors
  const zoneNames = Object.entries(groupedByZoneNames)
    .map(([zoneId, polygons]) => {
      const dissolved = dissolve(featureCollection(polygons));
      return dissolved.features.length < polygons.length ? zoneId : null;
    })
    .filter(Boolean);

  if (zoneNames.length > 0) {
    for (const x of zoneNames) {
      log(`${x} has neighbor with identical ID`);
    }
    throw new Error('Contains neighboring id zone');
  }
}

export function zeroOverlaps(
  fc: WorldFeatureCollection,
  { MIN_AREA_INTERSECTION }: GeoConfig
) {
  // add bbox to features to increase speed
  const features = getPolygons(fc).features.map((ft) => ({
    ft,
    bbox: bboxPolygon(bbox(ft)),
  }));

  const countriesToIgnore = new Set(
    fc.features
      .filter((ft) => ft.properties.isCombined)
      .map((ft) => ft.properties.countryKey)
  );

  // Since this code runs all the time and can be slow, we use this performance optimised version.
  // It creates a reverse loop of features and remove the tested one from the array to avoid
  // testing the same combination twice.
  for (let index1 = features.length - 1; index1 >= 0; index1--) {
    const ft1 = features[index1];
    if (countriesToIgnore.has(ft1.ft.properties?.countryKey)) {
      // We should not test this feature again
      features.pop();
      continue;
    }

    for (const [index2, ft2] of features.entries()) {
      if (index1 !== index2 && intersect(ft1.bbox, ft2.bbox)) {
        const intersection = intersect(ft1.ft, ft2.ft);
        if (intersection && area(intersection) > MIN_AREA_INTERSECTION) {
          throw new Error(
            `${ft1.ft.properties?.zoneName} overlaps with ${ft2.ft.properties?.zoneName}`
          );
        }
      }
    }
    // Remove the tested feature from the array
    features.pop();
  }
}

export { validateGeometry };
