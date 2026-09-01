import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getDiscoveredPatterns,
  proposeMapping,
  approveMapping,
  rejectMapping,
} from '../api/configsentinel'

export function useDiscoveredPatterns(params: {
  vendor?: string
  status?: string
  limit?: number
  offset?: number
  sort_by?: string
  sort_dir?: string
}) {
  return useQuery({
    queryKey: ['discoveredPatterns', params],
    queryFn: () => getDiscoveredPatterns(params),
  })
}

export function useProposeMapping() {
  return useMutation({
    mutationFn: (patternId: string) => proposeMapping(patternId),
  })
}

export function useApproveMapping() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (mappingId: string) => approveMapping(mappingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discoveredPatterns'] })
    },
  })
}

export function useRejectMapping() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (mappingId: string) => rejectMapping(mappingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discoveredPatterns'] })
    },
  })
}
