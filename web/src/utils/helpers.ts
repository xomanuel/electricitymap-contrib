import { callerLocation, useMeta } from 'api/getMeta';
import { useMatch, useParams } from 'react-router-dom';
import {
  ElectricityModeType,
  ElectricityStorageKeyType,
  GenerationType,
  StateZoneData,
  ZoneDetail,
} from 'types';

import zonesConfigJSON from '../../config/zones.json';
import { CombinedZonesConfig } from '../../geo/types';

export function useGetZoneFromPath() {
  const { zoneId } = useParams();
  const match = useMatch('/zone/:id');
  if (zoneId) {
    return zoneId;
  }
  return match?.params.id || undefined;
}

export function useUserLocation(): callerLocation {
  const { callerLocation } = useMeta();
  if (
    callerLocation &&
    callerLocation.length === 2 &&
    callerLocation.every((x) => Number.isFinite(x))
  ) {
    return callerLocation;
  }
  return null;
}

/**
 * Converts date to format returned by API
 */
export function dateToDatetimeString(date: Date) {
  return date.toISOString().split('.')[0] + 'Z';
}
export function getProductionCo2Intensity(
  mode: ElectricityModeType,
  zoneData: ZoneDetail
) {
  const isStorage = mode.includes('storage');
  const generationMode = mode.replace(' storage', '') as GenerationType;

  if (!isStorage) {
    return zoneData.productionCo2Intensities?.[generationMode];
  }

  const storageMode = generationMode as ElectricityStorageKeyType;
  const storage = zoneData.storage?.[storageMode];
  // If storing, we return 0 as we don't want to count it as CO2 emissions until electricity is discharged.
  if (storage && storage > 0) {
    return 0;
  }

  const dischargeCo2Intensity = zoneData.dischargeCo2Intensities?.[storageMode];
  return dischargeCo2Intensity;
}

/**
 * Returns a link which maintains search and hash parameters
 * @param to
 */

export function createToWithState(to: string, includeHash: boolean = false) {
  return `${to}${location.search}${includeHash ? location.hash : ''}`;
}

/**
 * Returns the fossil fuel ratio of a zone
 * @param isConsumption - Whether the ratio is for consumption or production
 * @param fossilFuelRatio - The fossil fuel ratio for consumption
 * @param fossilFuelRatioProduction - The fossil fuel ratio for production
 */
export function getFossilFuelRatio(
  zoneData: StateZoneData,
  isConsumption: boolean
): number {
  const fossilFuelRatioToUse = isConsumption ? zoneData?.c?.fr : zoneData?.p?.fr;
  switch (fossilFuelRatioToUse) {
    case 0: {
      return 1;
    }
    case 1: {
      return 0;
    }
    case null:
    case undefined: {
      return Number.NaN;
    }
    default: {
      return 1 - fossilFuelRatioToUse;
    }
  }
}

/**
 * Returns the carbon intensity of a zone
 * @param isConsumption - Whether the percentage is for consumption or production
 * @param co2intensity - The carbon intensity for consumption
 * @param co2intensityProduction - The carbon intensity for production
 */
export const getCarbonIntensity = (
  zoneData: StateZoneData,
  isConsumption: boolean
): number => (isConsumption ? zoneData?.c?.ci : zoneData?.p?.ci) ?? Number.NaN;

/**
 * Returns the renewable ratio of a zone
 * @param zoneData - The zone data
 * @param isConsumption - Whether the ratio is for consumption or production
 */
export const getRenewableRatio = (
  zoneData: StateZoneData,
  isConsumption: boolean
): number => (isConsumption ? zoneData?.c?.rr : zoneData?.p?.rr) ?? Number.NaN;

/**
 * Function to round a number to a specific amount of decimals.
 * @param {number} number - The number to round.
 * @param {number} decimals - Defaults to 2 decimals.
 * @returns {number} Rounded number.
 */
export const round = (number: number, decimals = 2): number =>
  (Math.round((Math.abs(number) + Number.EPSILON) * 10 ** decimals) / 10 ** decimals) *
  Math.sign(number);

/**
 * Returns the net exchange of a zone
 * @param zoneData - The zone data
 * @returns The net exchange
 */
export function getNetExchange(
  zoneData: ZoneDetail,
  displayByEmissions: boolean
): number {
  if (Object.keys(zoneData.exchange).length === 0) {
    return Number.NaN;
  }

  if (
    !displayByEmissions &&
    zoneData.totalImport === null &&
    zoneData.totalExport === null
  ) {
    return Number.NaN;
  }
  if (
    displayByEmissions &&
    zoneData.totalCo2Import == null &&
    zoneData.totalCo2Export == null
  ) {
    return Number.NaN;
  }

  const netExchangeValue = displayByEmissions
    ? round((zoneData.totalCo2Import ?? 0) - (zoneData.totalCo2Export ?? 0)) // in CO₂eq
    : round((zoneData.totalImport ?? 0) - (zoneData.totalExport ?? 0));

  return netExchangeValue;
}

export const getZoneTimezone = (zoneId?: string) => {
  if (!zoneId) {
    return undefined;
  }
  const { zones } = zonesConfigJSON as unknown as CombinedZonesConfig;
  return zones[zoneId]?.timezone;
};

/**
 * @returns {Boolean} true if agent is probably a mobile device.
 */
export const hasMobileUserAgent = () =>
  /android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i.test(
    navigator.userAgent
  );
