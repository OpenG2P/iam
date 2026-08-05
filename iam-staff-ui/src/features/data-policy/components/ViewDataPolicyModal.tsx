"use client";

import { useTranslations } from "next-intl";
import Modal from "@/components/Modal";
import { DataPolicy } from "../types";

interface ViewDataPolicyModalProps {
  onClose: () => void;
  data?: DataPolicy | null;
}

export default function ViewDataPolicyModal({ onClose, data }: ViewDataPolicyModalProps) {
  const t = useTranslations();

  if (!data) return null;

  const policyTargetLabel =
    data.policy_target === 'REGISTER_RECORD'
      ? 'Register Record'
      : data.policy_target === 'ATTRIBUTE'
        ? 'Attribute'
        : data.policy_target === 'GEO'
          ? 'Administrative Areas'
          : data.policy_target || '—';

  return (
    <Modal
      title={t('view_policy') || 'View Policy'}
      onClose={onClose}
      width="800"
    >
      <div className="space-y-4">
        <div className="grid grid-cols-[1.2fr_2fr] gap-4 py-2">
          <span className="text-gray-500 text-[16px] font-medium">
            {t('policy_mnemonic') || 'Policy Mnemonic'}
          </span>
          <div className="text-gray-900 text-[16px] font-normal break-all">
            {data.policy_mnemonic || '—'}
          </div>
        </div>

        <div className="py-2">
          <span className="text-gray-500 text-[16px] font-medium block mb-2">
            {t('policy_description') || 'Policy Description'}
          </span>
          <div className="text-gray-900 text-[16px] font-normal bg-gray-50 px-4 py-2 rounded-[10px] border border-gray-200 break-all">
            {data.policy_description || '—'}
          </div>
        </div>

        <div className="grid grid-cols-[1.2fr_2fr] gap-4 py-2">
          <span className="text-gray-500 text-[16px] font-medium">
            {t('policy_target') || 'Policy Target'}
          </span>
          <div className="text-gray-900 text-[16px] font-normal break-all">
            {policyTargetLabel}
          </div>
        </div>

        <div className="grid grid-cols-[1.2fr_2fr] gap-4 py-2">
          <span className="text-gray-500 text-[16px] font-medium">
            {t('policy_type') || 'Policy Type'}
          </span>
          <div className="text-gray-900 text-[16px] font-normal break-all">
            {data.policy_type || '—'}
          </div>
        </div>

        <div className="grid grid-cols-[1.2fr_2fr] gap-4 py-2">
          <span className="text-gray-500 text-[16px] font-medium">
            {t('policy_id') || 'Policy ID'}
          </span>
          <div className="text-gray-900 text-[16px] font-normal break-all">
            {data.policy_id || '—'}
          </div>
        </div>

        {data.register_id ? (
          <div className="grid grid-cols-[1.2fr_2fr] gap-4 py-2">
            <span className="text-gray-500 text-[16px] font-medium">
              {t('register_id') || 'Register ID'}
            </span>
            <div className="text-gray-900 text-[16px] font-normal break-all">
              {data.register_id}
            </div>
          </div>
        ) : null}

        <div className="py-2">
          <span className="text-gray-500 text-[16px] font-medium block mb-2">
            {t('policy_filter_expression') || 'Policy Filter Expression'}
          </span>
          <div className="text-gray-900 text-[14px] font-normal bg-gray-50 px-4 py-2 rounded-[10px] border border-gray-200 break-all font-mono">
            <pre className="whitespace-pre-wrap">
              {JSON.stringify(data.policy_filter_expression ?? {}, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </Modal>
  );
}
