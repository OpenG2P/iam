export interface DataPolicy {
  policy_id: string;
  policy_mnemonic: string;
  policy_description?: string | null;
  policy_target: string;
  policy_type: string;
  register_id?: string | null;
  application_id?: number | null;
  policy_filter_expression?: any;
  active?: boolean;
}
