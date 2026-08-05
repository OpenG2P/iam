"use client";

import { useEffect, useMemo, useState, use } from "react";
import Image from "next/image";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import { useSearchParams, useRouter } from "next/navigation";
import { useFetch } from "@/shared/hooks/useFetch";
import {
  useAllRegister,
  useAllAttributes,
  useG2pGeoLevels,
  useRegisterFields,
  type Register,
} from "@/features/data-policy/hooks";
import CustomDropdown from "@/features/data-policy/components/CustomDropdown";
import InputField from "@/components/InputField";
import TextAreaField from "@/components/TextAreaField";
import PolicyFilterExpressionBuilder, {
  canShowFilterBuilder,
} from "@/features/data-policy/components/PolicyFilterExpressionBuilder";
import AdministrativeAreasPolicyBuilder from "@/features/data-policy/components/AdministrativeAreasPolicyBuilder";
import PolicyFilterPreview from "@/features/data-policy/components/PolicyFilterPreview";
import { orderGeoLevelsByHierarchy } from "@/features/data-policy/utils/geoLevelUtils";
import { toGeoPolicyFilterExpression } from "@/features/data-policy/utils/geoLocationSerialization";
import type { GeoLocationSelection } from "@/features/data-policy/types/geoLocationTypes";
import {
  fromAttributes,
  fromRegisterFields,
} from "@/features/data-policy/utils/policyFilterFields";
import {
  createDefaultFilterRoot,
  serializeFilterExpression,
  validateFilterExpression,
  type FilterRootState,
} from "@/features/data-policy/utils/policyFilterExpression";

const POLICY_TYPES = ['ALLOW', 'DENY'] as const;

export default function CreateDataPolicyPage({ params }: { params: Promise<{ id: string }> }) {
  const t = useTranslations();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { execute: addPolicy } = useFetch();
  const { registers, loading: registersLoading } = useAllRegister(1, 100);

  const resolvedParams = use(params);
  const applicationId = parseInt(resolvedParams.id);
  const policyTarget = searchParams.get('policyTarget') || 'REGISTER_RECORD';
  const registerIdParam = searchParams.get('registerId') || '';

  const [registerId, setRegisterId] = useState(registerIdParam);
  const [policyMnemonic, setPolicyMnemonic] = useState('');
  const [policyDescription, setPolicyDescription] = useState('');
  const [policyType, setPolicyType] = useState<string>('ALLOW');
  const [filterRoot, setFilterRoot] = useState<FilterRootState>(createDefaultFilterRoot());
  const [geoLocations, setGeoLocations] = useState<GeoLocationSelection[]>([]);
  const [saving, setSaving] = useState(false);

  const isRegisterTarget = policyTarget === 'REGISTER_RECORD';
  const isGeoTarget = policyTarget === 'GEO';
  const isRegisterFixed = isRegisterTarget && !!registerIdParam;

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
    // Only auto-select first register if no register was passed as param
    if (!registerIdParam) {
      setRegisterId((current) => current || registers[0].register_id);
    }
  }, [isRegisterTarget, registers, registersLoading, registerIdParam]);

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
    router.back();
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

      if (result?.error) {
        toast.error(result.error);
        return;
      }

      toast.success('Data policy created successfully');
      router.back();
    } finally {
      setSaving(false);
    }
  };

  const showFilterBuilder = canShowFilterBuilder(policyTarget, registerId);

  return (
    <>
      <div className="flex flex-col gap-5 mb-6">
        <div className="bg-[#FFFFFF] rounded-[10px] p-6 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button
              onClick={handleCancel}
              className="w-9 h-9 rounded-[10px] bg-[#F3F1E4] hover:bg-[#E1E1E1] flex items-center justify-center transition-colors"
            >
              <Image src="/arrow_back_01.png" alt="Back" width={20} height={20} className="opacity-50" />
            </button>
            <div className="flex items-center gap-3">
              <div>
                <h1 className="text-lg font-semibold text-[#000000] m-0">Add Data Policy</h1>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleCancel}
              disabled={saving}
              className="px-5 h-8.5 rounded-[10px] bg-[#E1E1E1] text-[#000000]/70 text-sm font-semibold hover:bg-[#A1A1A1] transition-colors disabled:opacity-50"
            >
              {t('cancel')}
            </button>
            <button
              onClick={handleSubmit}
              disabled={saving}
              className="px-5 h-8.5 rounded-[10px] bg-[#000000] text-[#FFFFFF] text-sm font-semibold transition-colors shadow-lg disabled:opacity-50"
            >
              {saving ? t('saving') : t('save')}
            </button>
          </div>
        </div>

        <div className="bg-[#FFFFFF] rounded-[10px] p-6">
          <h2 className="text-base font-semibold text-[#000000] mb-4">
            {t('policy_details')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl">
            {isRegisterTarget ? (
              <CustomDropdown
                label={t('register')}
                options={registerOptions}
                value={registerId}
                onChange={setRegisterId}
                loading={registersLoading}
                placeholder={t('select_register')}
                disabled={isRegisterFixed}
              />
            ) : null}
            <CustomDropdown
              label={t('policy_type')}
              options={policyTypeOptions}
              value={policyType}
              onChange={setPolicyType}
            />
            <div className="md:col-span-2">
              <InputField
                label={t('policy_mnemonic')}
                value={policyMnemonic}
                onChange={setPolicyMnemonic}
                placeholder={t('enter_policy_mnemonic')}
              />
            </div>
            <div className="md:col-span-2">
              <TextAreaField
                label={t('policy_description')}
                value={policyDescription}
                onChange={setPolicyDescription}
                placeholder={t('enter_policy_description')}
              />
            </div>
          </div>
        </div>

        <div className="bg-[#FFFFFF] rounded-[10px] p-6">
          <h2 className="text-base font-semibold text-[#000000] mb-4">
            {t('filter_rules')}
          </h2>
          {!showFilterBuilder ? (
            <p className="text-[16px] text-gray-500">
              {isRegisterTarget ? t('select_register_for_filter_fields') : t('loading_filter_fields')}
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
      </div>
    </>
  );
}
