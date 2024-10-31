import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtom } from 'jotai';
import invariant from 'tiny-invariant';
import type { ZoneDetails } from 'types';
import { TimeAverages } from 'utils/constants';
import { useGetZoneFromPath } from 'utils/helpers';
import { timeAverageAtom } from 'utils/state/atoms';

import { cacheBuster, getBasePath, getHeaders, QUERY_KEYS } from './helpers';

const getZone = async (
  timeAverage: TimeAverages,
  zoneId?: string
): Promise<ZoneDetails> => {
  invariant(zoneId, 'Zone ID is required');
  const path: URL = new URL(`v8/details/${timeAverage}/${zoneId}`, getBasePath());
  path.searchParams.append('cacheKey', cacheBuster());

  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  const response = await fetch(path, requestOptions);

  if (response.ok) {
    const { data } = (await response.json()) as { data: ZoneDetails };
    if (!data.zoneStates) {
      throw new Error('No data returned from API');
    }
    return data;
  }

  throw new Error(await response.text());
};

// TODO: The frontend (graphs) expects that the datetimes in state are the same as in zone
// should we add a check for this?
const useGetZone = (): UseQueryResult<ZoneDetails> => {
  const zoneId = useGetZoneFromPath();
  const [timeAverage] = useAtom(timeAverageAtom);
  return useQuery<ZoneDetails>({
    queryKey: [QUERY_KEYS.ZONE, { zone: zoneId, aggregate: timeAverage }],
    queryFn: async () => getZone(timeAverage, zoneId),
  });
};

export default useGetZone;
