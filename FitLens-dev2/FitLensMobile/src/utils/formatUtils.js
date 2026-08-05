export const formatCm = (val) => {
  if (val === undefined || val === null || isNaN(val)) return '--';
  return `${parseFloat(val).toFixed(1)} cm`;
};

export const formatInch = (cmVal) => {
  if (cmVal === undefined || cmVal === null || isNaN(cmVal)) return '--';
  const inches = parseFloat(cmVal) / 2.54;
  return `${inches.toFixed(1)} in`;
};

export const formatDate = (dateStr) => {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch (e) {
    return dateStr;
  }
};

export const cmToFeetInches = (cm) => {
  if (!cm || isNaN(cm)) return { feet: 5, inches: 7 };
  const totalInches = cm / 2.54;
  const feet = Math.floor(totalInches / 12);
  const inches = Math.round(totalInches % 12);
  return { feet, inches };
};

export const feetInchesToCm = (feet, inches) => {
  const f = parseFloat(feet) || 0;
  const i = parseFloat(inches) || 0;
  return Math.round((f * 12 + i) * 2.54 * 10) / 10;
};
