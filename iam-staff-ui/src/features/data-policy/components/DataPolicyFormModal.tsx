"use client";

import { useEffect, useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import { useFetch } from "@/shared/hooks/useFetch";
import {
    useAllRegister,
    useAllAttributes,
    useG2pGeoLevels,
    useRegisterFields,
    type Register,
} from "../hooks/index";
import CustomDropdown from "./CustomDropdown";
import InputField from "@/components/InputField";
import TextAreaField from "@/components/TextAreaField";
import PolicyFilterExpressionBuilder, {
    canShowFilterBuilder,
} from "./PolicyFilterExpressionBuilder";
import AdministrativeAreasPolicyBuilder from "./AdministrativeAreasPolicyBuilder";
import PolicyFilterPreview from "./PolicyFilterPreview";
import { orderGeoLevelsByHierarchy } from "../utils/geoLevelUtils";
import { toGeoPolicyFilterExpression } from "../utils/geoLocationSerialization";
import type { GeoLocationSelection } from "../types/geoLocationTypes";
import {
    fromAttributes,
    fromRegisterFields,
} from "../utils/policyFilterFields";
import {
    createDefaultFilterRoot,
    serializeFilterExpression,
    validateFilterExpression,
    type FilterRootState,
} from "../utils/policyFilterExpression";

const POLICY_TYPES = ['ALLOW', 'DENY'] as const;

interface DataPolicyFormModalProps {
  applicationId: number;
  policyTarget: string;
  registerId?: string;
  onClose: () => void;
  onSuccess: () => void;
}

export function DataPolicyFormModal({
  applicationId,
  policyTarget,
  registerId: propRegisterId,
  onClose,
  onSuccess,
}: DataPolicyFormModalProps) {
  const t = useTranslations();
  const { execute: addPolicy } = useFetch();
  const { registers, loading: registersLoading } = useAllRegister(1, 100);

  const [registerId, setRegisterId] = useState(propRegisterId || '');
  const [policyMnemonic, setPolicyMnemonic] = useState('');
  const [policyDescription, setPolicyDescription] = useState('');
  const [policyType, setPolicyType] = useState<string>('ALLOW');
  const [filterRoot, setFilterRoot] = useState<FilterRootState>(createDefaultFilterRoot());
  const [geoLocations, setGeoLocations] = useState<GeoLocationSelection[]>([]);
  const [saving, setSaving] = useState(false);

  const isRegisterTarget = policyTarget === 'REGISTER_RECORD';
  const isGeoTarget = policyTarget === 'GEO';
  const isRegisterFixed = isRegisterTarget && !!propRegisterId;

  const { fields: registerFields, loading: registerFieldsLoading } = useRegisterFields(
    isRegisterTarget ? registerId : '',
  );
  const { attributes, loading: attributesLoading } = useAllAttributes(1, 500);
  const { geoLevels: g2pGeoLevels, loading: g2pGeoLevelsLoading } = useG2pGeoLevels();
  const orderedGeoLevels = useMemo(
    () => orderGeoLevelsByHierarchy(g2pGeoLevels),
    [g2pGeoLevels],
  );

  useEffect(() => {
    if (!isRegisterTarget || registersLoading || !registers?.length) {
      return;
    }
    // Only auto-select first register if no register was passed as prop
    if (!propRegisterId) {
      setRegisterId((current) => current || registers[0].register_id);
    }
  }, [isRegisterTarget, registers, registersLoading, propRegisterId]);

  useEffect(() => {
    if (isGeoTarget) {
      setGeoLocations([]);
      return;
    }
    setFilterRoot(createDefaultFilterRoot());
  }, [registerId, policyTarget, isGeoTarget]);

  const registerOptions = useMemo(
    () =>
      (registers || []).map((register: Register) => ({
        label: register.register_mnemonic || register.register_id,
        value: register.register_id,
      })),
    [registers],
  );

  const policyTypeOptions = useMemo(
    () => POLICY_TYPES.map((type) => ({ label: type, value: type })),
    [],
  );

  const filterFields = useMemo(() => {
    if (policyTarget === 'ATTRIBUTE') {
      return fromAttributes(attributes);
    }
    return fromRegisterFields(registerFields);
  }, [policyTarget, attributes, registerFields]);

  const fieldsLoading = useMemo(() => {
    if (policyTarget === 'ATTRIBUTE') return attributesLoading;
    return registerFieldsLoading;
  }, [policyTarget, attributesLoading, registerFieldsLoading]);

  const handleCancel = () => {
    onClose();
  };

  const handleSubmit = async () => {
    if (isRegisterTarget && !registerId) {
      toast.warn(t('register_required'));
      return;
    }
    if (!policyMnemonic.trim()) {
      toast.warn(t('policy_mnemonic_required'));
      return;
    }
    if (isGeoTarget) {
      if (geoLocations.length === 0) {
        toast.warn(t('policy_filter_expression_required'));
        return;
      }
    } else if (!validateFilterExpression(filterRoot)) {
      toast.warn(t('policy_filter_expression_required'));
      return;
    }

    setSaving(true);
    try {
      const policyFilterExpression = isGeoTarget
        ? toGeoPolicyFilterExpression(geoLocations)
        : serializeFilterExpression(filterRoot, filterFields);

      const result = await addPolicy('/api/applications/data-policies/add', {
        method: 'POST',
        body: JSON.stringify({
          register_id: policyTarget === 'REGISTER_RECORD' ? registerId : null,
          policy_target: policyTarget,
          policy_mnemonic: policyMnemonic.trim(),
          policy_description: policyDescription.trim(),
          policy_type: policyType,
          policy_filter_expression: policyFilterExpression,
          application_id: applicationId,
        }),
      });

      console.log('Add policy result:', result);

      if (result?.error) {
        toast.error(result.error);
        return;
      }

      toast.success('Data policy created successfully');
      onSuccess();
    } finally {
      setSaving(false);
    }
  };

  const showFilterBuilder = canShowFilterBuilder(policyTarget, registerId);

  return (
    <div className="fixed inset-0 bg-[#000000]/80 z-50 flex items-center justify-center p-6">
      <div className="relative w-full max-w-6xl bg-[#FFFFFF] rounded-[10px] border-[5px] border-[#EABB13] px-8 py-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[24px] text-[#ED7C22] font-medium">Add Data Policy</h2>
          <button
            type="button"
            onClick={onClose}
            className="opacity-50 hover:opacity-100 transition"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4 max-h-[70vh] overflow-y-auto modal-scroll">
          <div className="bg-[#F3F1E4] rounded-lg p-6">
            <h3 className="text-base font-semibold mb-4">Policy Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl">
              {isRegisterTarget ? (
                <CustomDropdown
                  label="Register"
                  options={registerOptions}
                  value={registerId}
                  onChange={setRegisterId}
                  loading={registersLoading}
                  placeholder="Select register"
                  disabled={isRegisterFixed}
                />
              ) : null}
              <CustomDropdown
                label="Policy Type"
                options={policyTypeOptions}
                value={policyType}
                onChange={setPolicyType}
              />
              <div className="md:col-span-2">
                <InputField
                  label="Policy Mnemonic"
                  value={policyMnemonic}
                  onChange={setPolicyMnemonic}
                  placeholder="Enter policy mnemonic"
                />
              </div>
              <div className="md:col-span-2">
                <TextAreaField
                  label="Policy Description"
                  value={policyDescription}
                  onChange={setPolicyDescription}
                  placeholder="Enter policy description"
                />
              </div>
            </div>
          </div>

          <div className="bg-[#F3F1E4] rounded-lg p-6">
            <h3 className="text-base font-semibold mb-4">Filter Rules</h3>
            {!showFilterBuilder ? (
              <p className="text-[16px] text-gray-500">
                {isRegisterTarget ? 'Select a register to view filter fields' : 'Loading filter fields...'}
              </p>
            ) : (
              <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(280px,340px)] gap-6 items-stretch">
                {isGeoTarget ? (
                  <AdministrativeAreasPolicyBuilder
                    geoLevels={orderedGeoLevels}
                    geoLevelsLoading={g2pGeoLevelsLoading}
                    locations={geoLocations}
                    onChange={setGeoLocations}
                  />
                ) : (
                  <PolicyFilterExpressionBuilder
                    root={filterRoot}
                    policyTarget={policyTarget}
                    fields={filterFields}
                    fieldsLoading={fieldsLoading}
                    onChange={setFilterRoot}
                  />
                )}
                <div className="xl:sticky xl:top-4 flex flex-col min-h-full">
                  {isGeoTarget ? (
                    <PolicyFilterPreview root={filterRoot} fields={filterFields} />
                  ) : (
                    <PolicyFilterPreview root={filterRoot} fields={filterFields} />
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-4 pt-2">
            <button
              type="button"
              onClick={handleCancel}
              disabled={saving}
              className="px-6 py-2 bg-[#E1E1E1] text-[#000000]/50 text-[16px] font-bold rounded-[10px] disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={saving}
              className="px-6 py-2 bg-[#000000] text-[#FFFFFF] text-[16px] font-bold rounded-[10px] disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
