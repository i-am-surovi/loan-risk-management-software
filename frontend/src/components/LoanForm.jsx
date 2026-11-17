import { useEffect, useState } from "react";

function LoanForm() {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [product, setProduct] = useState(null);
  const [productLoading, setProductLoading] = useState(true);
  const [productError, setProductError] = useState("");

  const [formData, setFormData] = useState({
    Age: "",
    Income: "",
    LoanAmount: "",
    CreditScore: "",
    MonthsEmployed: "",
    NumCreditLines: "",
    InterestRate: "",
    LoanTerm: "",
    DTIRatio: "",
    HasCreditHistory: "Yes",
    Education: "Bachelor's",
    EmploymentType: "Full-time",
    MaritalStatus: "Single",
    HasMortgage: "No",
    HasDependents: "No",
    LoanPurpose: "Other",
    HasCoSigner: "No",
  });

  // Load active Personal Loan product from the database
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

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

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

    // No credit history: current model cannot reliably assess.
    if (formData.HasCreditHistory === "No") {
      setPrediction({
        manual_review: true,
        risk: "Manual Review",
        message:
          "The applicant has no credit history. Manual assessment is required because the current AI model was not trained on applicants without credit history.",
      });
      return;
    }

    try {
      setLoading(true);

      const response = await fetch("http://127.0.0.1:8000/api/v1/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...formData,
          Age: Number(formData.Age),
          Income: Number(formData.Income),
          LoanAmount: Number(formData.LoanAmount),
          CreditScore: Number(formData.CreditScore),
          MonthsEmployed: Number(formData.MonthsEmployed),
          NumCreditLines: Number(formData.NumCreditLines),
          InterestRate: Number(product.annual_interest_rate),
          LoanTerm: Number(formData.LoanTerm),
          DTIRatio: Number(formData.DTIRatio),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(JSON.stringify(data));
      }

      setPrediction(data);
    } catch (error) {
      console.error("Prediction Error:", error);
      alert("Prediction failed. Please check the backend.");
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { name: "Age", label: "Applicant Age" },
    { name: "Income", label: "Annual Income" },
    { name: "LoanAmount", label: "Loan Amount" },
    { name: "MonthsEmployed", label: "Months Employed" },
    { name: "LoanTerm", label: "Loan Term (Months)" },
    {
      name: "DTIRatio",
      label: "Debt-to-Income Ratio",
      step: "0.01",
    },
  ];

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
        Enter applicant information to assess loan default risk.
      </p>

      {productLoading && (
        <p className="text-blue-600 mb-4">
          Loading loan product information...
        </p>
      )}

      {productError && <p className="text-red-600 mb-4">{productError}</p>}

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Applicant Information */}
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

        <button
          type="submit"
          disabled={loading || productLoading || !product}
          className="mt-8 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-medium px-8 py-3 rounded-lg"
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
