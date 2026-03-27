import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { devicesApi } from "@/services/devicesApi";
import { getErrorMessage } from "@/services/api";
import type { DeviceCreate } from "@/types";

export function useDevices() {
  return useQuery({
    queryKey: ["devices"],
    queryFn: () => devicesApi.list(),
    refetchInterval: 15_000,
  });
}

export function useDeviceHealth(id: number) {
  return useQuery({
    queryKey: ["device-health", id],
    queryFn: () => devicesApi.health(id),
    refetchInterval: 15_000,
  });
}

export function useCreateDevice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DeviceCreate) => devicesApi.create(data),
    onSuccess: () => {
      toast.success("Qurilma qo'shildi");
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useUpdateDevice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<DeviceCreate> }) =>
      devicesApi.update(id, data),
    onSuccess: () => {
      toast.success("Qurilma yangilandi");
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useDeleteDevice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => devicesApi.delete(id),
    onSuccess: () => {
      toast.success("Qurilma o'chirildi");
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useSyncDevice() {
  return useMutation({
    mutationFn: (id: number) => devicesApi.sync(id),
    onSuccess: () => toast.success("Sinxronlash boshlandi"),
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}
