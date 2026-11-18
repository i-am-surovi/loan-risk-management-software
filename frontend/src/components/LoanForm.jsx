import { useEffect, useState } from "react";

function LoanForm({ onPredictionSuccess }) {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  const [product, setProduct] = useState(null);
  const [productLoading, setProductLoading] = useState(true);
  const [productError, setProductError] = useState("");

  const [calculation, setCalculation] = useState(null);
  const [calculationLoading, setCalculationLoading] = useState(false);
  const [calculationError, setCalculationError] = useState("");

  const [formData, setFormData] = useState({
    Age: "",
    Income: "",
    LoanAmount: "",
    CreditScore: "",
    MonthsEmployed: "",
    NumCreditLines: "",
    InterestRate: "",
    LoanTerm: "",
    ExistingMonthlyDebt: "",
    HasCreditHistory: "Yes",
    Education: "Bachelor's",
    EmploymentType: "Full-time",
    MaritalStatus: "Single",
    HasMortgage: "No",
    HasDependents: "No",
    LoanPurpose: "Other",
    HasCoSigner: "No",
  });

  // Load active Personal Loan product
  useEffect(() => {
    const fetchProduct = async () => {
      try {
        setProductLoading(true);
        setProductError("");

        const response = await fetch("http://127.0.0.1:8000/api/v1/products");

        if (!response.ok) {
          throw new Error("Could not load loan products.");
        }

        const data = await response.json();

        const personalLoan = (data.products || []).find(
          (item) =>
            item.product_name === "Personal Loan" && item.is_active === true,
        );

        if (!personalLoan) {
          throw new Error("No active Personal Loan product found.");
        }

        setProduct(personalLoan);

        setFormData((prev) => ({
          ...prev,
          InterestRate: String(personalLoan.annual_interest_rate),
        }));
      } catch (error) {
        console.error("Product Loading Error:", error);
        setProductError(error.message);
      } finally {
        setProductLoading(false);
      }
    };

    fetchProduct();
  }, []);

  // Handle form changes
  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    setCalculation(null);
    setCalculationError("");
    setPrediction(null);
  };

  // Calculate actual EMI and DTI
  const handleCalculate = async () => {
    if (
      !product ||
      !formData.Income ||
      !formData.LoanAmount ||
      !formData.LoanTerm ||
      formData.ExistingMonthlyDebt === ""
    ) {
      setCalculationError(
        "Please enter Annual Income, Loan Amount, Loan Term and Existing Monthly Debt.",
      );
      return;
    }

    try {
      setCalculationLoading(true);
      setCalculationError("");
      setCalculation(null);
      setPrediction(null);

      const response = await fetch(
        "http://127.0.0.1:8000/api/v1/calculate-loan",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            product_id: product.id,
            annual_income: Number(formData.Income),
            loan_amount: Number(formData.LoanAmount),
            loan_term_months: Number(formData.LoanTerm),
            existing_monthly_debt: Number(formData.ExistingMonthlyDebt),
          }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail || data),
        );
      }

      setCalculation(data);
    } catch (error) {
      console.error("Calculation Error:", error);
      setCalculationError(error.message);
    } finally {
      setCalculationLoading(false);
    }
  };

  // Submit prediction
  const handleSubmit = async (e) => {
    e.preventDefault();
    setPrediction(null);

    if (productLoading) {
      alert("Please wait. Loading loan product...");
      return;
    }

    if (!product) {
      alert("Loan product is unavailable. Please try again later.");
      return;
    }

    if (!calculation) {
      alert("Please calculate EMI and DTI before prediction.");
      return;
    }

    // Applicants without credit history require manual review
    if (formData.HasCreditHistory === "No") {
      setPrediction({
        manual_review: true,
        risk: "Manual Review",
        message:
          "The applicant has no credit history. Manual assessment is required because the current AI model was not trained on applicants without credit history.",
      });
      return;
    }

    // Validate required prediction fields
    if (
      !formData.Age ||
      !formData.CreditScore ||
      !formData.NumCreditLines ||
      !formData.MonthsEmployed
    ) {
      alert("Please complete all applicant information.");
      return;
    }

    try {
      setLoading(true);

      // Send only the 15 features used by the trained model
      const predictionPayload = {
        Age: Number(formData.Age),
        Income: Number(formData.Income),
        LoanAmount: Number(formData.LoanAmount),
        CreditScore: Number(formData.CreditScore),
        MonthsEmployed: Number(formData.MonthsEmployed),
        NumCreditLines: Number(formData.NumCreditLines),
        InterestRate: Number(product.annual_interest_rate),
        LoanTerm: Number(formData.LoanTerm),

        Education: formData.Education,
        EmploymentType: formData.EmploymentType,
        MaritalStatus: formData.MaritalStatus,
        HasMortgage: formData.HasMortgage,
        HasDependents: formData.HasDependents,
        LoanPurpose: formData.LoanPurpose,
        HasCoSigner: formData.HasCoSigner,
      };

      const response = await fetch("http://127.0.0.1:8000/api/v1/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(predictionPayload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail || data),
        );
      }

      setPrediction(data);

      if (onPredictionSuccess) {
        await onPredictionSuccess();
      }
    } catch (error) {
      console.error("Prediction Error:", error);
      alert(error.message || "Prediction failed. Please check the backend.");
    } finally {
      setLoading(false);
    }
  };

  // DTI Financial Warning System
  const getDTIWarning = (dti) => {
    if (dti <= 30) {
      return {
        level: "Low Debt Burden",
        message: "The applicant has a relatively low debt burden.",
        color: "green",
      };
    }

    if (dti <= 40) {
      return {
        level: "Moderate Debt Burden",
        message: "The applicant has a moderate debt burden.",
        color: "yellow",
      };
    }

    if (dti <= 50) {
      return {
        level: "High Debt Burden",
        message:
          "The applicant has a high debt burden. Further financial assessment is recommended.",
        color: "orange",
      };
    }

    return {
      level: "Very High Debt Burden",
      message:
        "The applicant's monthly debt obligations exceed 50% of monthly income. Careful financial assessment is strongly recommended.",
      color: "red",
    };
  };

  // Input fields
  const fields = [
    { name: "Age", label: "Applicant Age" },
    { name: "Income", label: "Annual Income" },
    { name: "LoanAmount", label: "Loan Amount" },
    { name: "MonthsEmployed", label: "Months Employed" },
    { name: "LoanTerm", label: "Loan Term (Months)" },
    {
      name: "ExistingMonthlyDebt",
      label: "Existing Monthly Debt",
      step: "0.01",
    },
  ];

  // Dropdown fields
  const dropdowns = [
    {
      name: "Education",
      label: "Education",
      options: ["Bachelor's", "High School", "Master's", "PhD"],
    },
    {
      name: "EmploymentType",
      label: "Employment Type",
      options: ["Full-time", "Part-time", "Self-employed", "Unemployed"],
    },
    {
      name: "MaritalStatus",
      label: "Marital Status",
      options: ["Divorced", "Married", "Single"],
    },
    {
      name: "HasMortgage",
      label: "Has Mortgage?",
      options: ["No", "Yes"],
    },
    {
      name: "HasDependents",
      label: "Has Dependents?",
      options: ["No", "Yes"],
    },
    {
      name: "LoanPurpose",
      label: "Loan Purpose",
      options: ["Auto", "Business", "Education", "Home", "Other"],
    },
    {
      name: "HasCoSigner",
      label: "Has Co-Signer?",
      options: ["No", "Yes"],
    },
  ];

  return (
    <section className="bg-white p-8 rounded-xl shadow-sm">
      <h2 className="text-2xl font-bold text-slate-800 mb-2">
        Personal Loan Assessment
      </h2>

      <p className="text-slate-500 mb-8">
        Enter applicant information to calculate loan installment and assess
        default risk.
      </p>

      {productLoading && (
        <p className="text-blue-600 mb-4">
          Loading loan product information...
        </p>
      )}

      {productError && <p className="text-red-600 mb-4">{productError}</p>}

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {fields.map((field) => (
            <div key={field.name}>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                {field.label}
              </label>

              <input
                type="number"
                name={field.name}
                value={formData[field.name]}
                onChange={handleChange}
                step={field.step || "1"}
                min="0"
                required
                className="w-full border border-slate-300 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          ))}

          {/* Automatically Loaded Interest Rate */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Annual Interest Rate (%)
            </label>

            <input
              type="number"
              value={product ? product.annual_interest_rate : ""}
              readOnly
              className="w-full border border-slate-300 rounded-lg px-4 py-3 bg-slate-100 text-slate-700 cursor-not-allowed"
            />

            <p className="text-xs text-slate-500 mt-1">
              Automatically set by the loan product.
            </p>
          </div>

          {/* Credit History */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Does the applicant have a credit history?
            </label>

            <select
              name="HasCreditHistory"
              value={formData.HasCreditHistory}
              onChange={handleChange}
              className="w-full border border-slate-300 rounded-lg px-4 py-3 bg-white"
            >
              <option value="Yes">Yes</option>
              <option value="No">No</option>
            </select>
          </div>

          {/* Credit Information */}
          {formData.HasCreditHistory === "Yes" && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Credit Score (From Credit Bureau)
                </label>

                <input
                  type="number"
                  name="CreditScore"
                  value={formData.CreditScore}
                  onChange={handleChange}
                  min="300"
                  max="849"
                  required
                  placeholder="e.g. 650"
                  className="w-full border border-slate-300 rounded-lg px-4 py-3"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Number of Credit Lines
                </label>

                <input
                  type="number"
                  name="NumCreditLines"
                  value={formData.NumCreditLines}
                  onChange={handleChange}
                  min="1"
                  required
                  placeholder="e.g. 2"
                  className="w-full border border-slate-300 rounded-lg px-4 py-3"
                />
              </div>
            </>
          )}

          {/* Other Applicant Information */}
          {dropdowns.map((field) => (
            <div key={field.name}>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                {field.label}
              </label>

              <select
                name={field.name}
                value={formData[field.name]}
                onChange={handleChange}
                className="w-full border border-slate-300 rounded-lg px-4 py-3 bg-white"
              >
                {field.options.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>

        {/* Calculate EMI and DTI */}
        <button
          type="button"
          onClick={handleCalculate}
          disabled={calculationLoading || productLoading || !product}
          className="mt-8 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white font-medium px-8 py-3 rounded-lg"
        >
          {calculationLoading ? "Calculating..." : "Calculate EMI & DTI"}
        </button>

        {calculationError && (
          <p className="mt-4 text-red-600">{calculationError}</p>
        )}

        {/* Calculation Result */}
        {calculation && (
          <div className="mt-6 p-6 rounded-xl border border-indigo-200 bg-indigo-50">
            <h3 className="text-xl font-bold text-slate-800 mb-4">
              Loan Calculation Summary
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <p>
                Monthly Income:{" "}
                <strong>৳{calculation.monthly_income.toLocaleString()}</strong>
              </p>

              <p>
                Monthly EMI:{" "}
                <strong>
                  ৳{calculation.monthly_installment.toLocaleString()}
                </strong>
              </p>

              <p>
                Existing Monthly Debt:{" "}
                <strong>
                  ৳{calculation.existing_monthly_debt.toLocaleString()}
                </strong>
              </p>

              <p>
                Total Monthly Debt:{" "}
                <strong>
                  ৳{calculation.total_monthly_debt.toLocaleString()}
                </strong>
              </p>

              <p>
                Actual DTI:{" "}
                <strong className="text-indigo-700">
                  {calculation.dti_percentage}%
                </strong>
              </p>

              {(() => {
                const warning = getDTIWarning(calculation.dti_percentage);

                const colors = {
                  green: "bg-green-100 text-green-800 border-green-300",
                  yellow: "bg-yellow-100 text-yellow-800 border-yellow-300",
                  orange: "bg-orange-100 text-orange-800 border-orange-300",
                  red: "bg-red-100 text-red-800 border-red-300",
                };

                return (
                  <div
                    className={`mt-4 p-4 rounded-lg border ${colors[warning.color]}`}
                  >
                    <h4 className="font-bold">
                      Financial Warning: {warning.level}
                    </h4>

                    <p className="text-sm mt-1">{warning.message}</p>
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* Predict Loan Risk */}
        <button
          type="submit"
          disabled={loading || productLoading || !product || !calculation}
          className="mt-6 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-medium px-8 py-3 rounded-lg"
        >
          {loading ? "Analyzing..." : "Predict Loan Risk"}
        </button>
      </form>

      {/* Prediction Result */}
      {prediction && (
        <div className="mt-8 p-6 rounded-xl border border-slate-200 bg-slate-50">
          {prediction.manual_review ? (
            <>
              <h3 className="text-xl font-bold text-orange-600 mb-3">
                Manual Review Required
              </h3>

              <p className="text-slate-600">{prediction.message}</p>
            </>
          ) : (
            <>
              <h3 className="text-xl font-bold text-slate-800 mb-4">
                Loan Risk Assessment Result
              </h3>

              <p className="text-slate-600 mb-2">
                Default Probability:
                <span className="font-bold ml-2">
                  {(prediction.default_probability * 100).toFixed(2)}%
                </span>
              </p>

              <p className="text-slate-600 mb-2">
                Risk Level:
                <span
                  className={`font-bold ml-2 ${
                    prediction.risk === "High Risk"
                      ? "text-red-600"
                      : "text-green-600"
                  }`}
                >
                  {prediction.risk}
                </span>
              </p>

              <p className="text-slate-600">Prediction ID: {prediction.id}</p>
            </>
          )}
        </div>
      )}
    </section>
  );
}

export default LoanForm;
