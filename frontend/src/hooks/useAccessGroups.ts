import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { accessGroupsApi } from "@/services/accessGroupsApi";
import { getErrorMessage } from "@/services/api";
import type { AccessGroupCreate, AccessGroupUpdate } from "@/types";

export function useAccessGroups() {
  return useQuery({
    queryKey: ["access-groups"],
    queryFn: () => accessGroupsApi.list(),
  });
}

export function useAccessGroup(id: number | null) {
  return useQuery({
    queryKey: ["access-groups", id],
    queryFn: () => accessGroupsApi.get(id!),
    enabled: id !== null,
  });
}

export function useCreateAccessGroup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: AccessGroupCreate) => accessGroupsApi.create(data),
    onSuccess: () => {
      toast.success("Kirish guruhi yaratildi");
      qc.invalidateQueries({ queryKey: ["access-groups"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useUpdateAccessGroup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AccessGroupUpdate }) =>
      accessGroupsApi.update(id, data),
    onSuccess: () => {
      toast.success("Kirish guruhi yangilandi");
      qc.invalidateQueries({ queryKey: ["access-groups"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useDeleteAccessGroup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => accessGroupsApi.delete(id),
    onSuccess: () => {
      toast.success("Kirish guruhi o'chirildi");
      qc.invalidateQueries({ queryKey: ["access-groups"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useAddGroupDevice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ groupId, deviceId }: { groupId: number; deviceId: number }) =>
      accessGroupsApi.addDevice(groupId, deviceId),
    onSuccess: (_data, { groupId }) => {
      toast.success("Qurilma qo'shildi");
      qc.invalidateQueries({ queryKey: ["access-groups", groupId] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useRemoveGroupDevice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ groupId, deviceId }: { groupId: number; deviceId: number }) =>
      accessGroupsApi.removeDevice(groupId, deviceId),
    onSuccess: (_data, { groupId }) => {
      toast.success("Qurilma o'chirildi");
      qc.invalidateQueries({ queryKey: ["access-groups", groupId] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useAddGroupStudent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ groupId, studentId }: { groupId: number; studentId: string }) =>
      accessGroupsApi.addStudent(groupId, studentId),
    onSuccess: (_data, { groupId }) => {
      toast.success("O'quvchi qo'shildi, sinxronlash boshlandi");
      qc.invalidateQueries({ queryKey: ["access-groups", groupId] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useRemoveGroupStudent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ groupId, studentId }: { groupId: number; studentId: string }) =>
      accessGroupsApi.removeStudent(groupId, studentId),
    onSuccess: (_data, { groupId }) => {
      toast.success("O'quvchi o'chirildi");
      qc.invalidateQueries({ queryKey: ["access-groups", groupId] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useRetryStudentSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ groupId, studentId }: { groupId: number; studentId: string }) =>
      accessGroupsApi.retryStudentSync(groupId, studentId),
    onSuccess: (_data, { groupId }) => {
      toast.success("Sinxronlash qayta boshlandi");
      qc.invalidateQueries({ queryKey: ["access-groups", groupId] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useAddGroupCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      groupId,
      categoryId,
    }: {
      groupId: number;
      categoryId: number;
    }) => accessGroupsApi.addCategory(groupId, categoryId),
    onSuccess: (res, { groupId }) => {
      const d = res.data.data;
      toast.success(
        `${d.added} ta o'quvchi qo'shildi, ${d.skipped} ta allaqachon guruhda`,
      );
      qc.invalidateQueries({ queryKey: ["access-groups", groupId] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useSyncGroup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => accessGroupsApi.sync(id),
    onSuccess: (_data, id) => {
      toast.success("Sinxronlash boshlandi");
      qc.invalidateQueries({ queryKey: ["access-groups", id] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}
