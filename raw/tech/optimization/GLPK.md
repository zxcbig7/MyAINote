# GLPK

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Linq;
using org.gnu.glpk;

namespace GLPKEngine
{

    public class GLPKBasic : IGlpkCallbackListener, IGlpkTerminalListener, IDisposable
    {
        private bool hookUsed = true;

        public glp_prob lp;
        public glp_smcp parm;
        public glp_tran tran;
        public glp_iocp iocp;

        public SWIGTYPE_p_double doubleVar;
        public SWIGTYPE_p_double doubleSol;
        public SWIGTYPE_p_int intVar;
        public SWIGTYPE_p_int intSol;

        public int skip = 0;
        public int ret;

        public GLPKBasic()
        {

        }

        public void show_version()
        {
            Console.WriteLine("GLPK " + GLPK.glp_version());
        }

        public void build_model()
        {
            // Listen to callbacks
            GlpkCallback.addListener(this);
            // Listen to terminal output
            GlpkTerminal.addListener(this);

            this.lp = GLPK.glp_create_prob();
            Console.WriteLine("Problem created.");
        }

        public void read_model(string file_name)
        {
            // create problem
            this.lp = GLPK.glp_create_prob();

            // allocate workspace
            this.tran = GLPK.glp_mpl_alloc_wksp();

            // read model
            this.ret = GLPK.glp_mpl_read_model(this.tran, file_name, skip);
            if (ret != 0)
            {
                GLPK.glp_mpl_free_wksp(this.tran);
                GLPK.glp_delete_prob(this.lp);
                throw new ApplicationException("Model file not valid: " + file_name);
            }

            // generate model
            ret = GLPK.glp_mpl_generate(tran, null);
            if (ret != 0)
            {
                GLPK.glp_mpl_free_wksp(this.tran);
                GLPK.glp_delete_prob(this.lp);
                throw new ApplicationException("Cannot generate model: " + file_name);
            }

            // Build model
            GLPK.glp_mpl_build_prob(this.tran, this.lp);
        }

        public void Set_parameters()
        {
            // Set solver parameters
            this.iocp = new glp_iocp();
            GLPK.glp_init_iocp(this.iocp);

            this.iocp.alien = 0;
            this.iocp.sr_heur = 0;

            // 預處理: GLPK.GLP_ON / GLPK.GLP_OFF
            this.iocp.presolve = GLPK.GLP_ON;

            // 時間限制(毫秒):
            this.iocp.tm_lim = 60 * 60 * 1000;

            // MIP_GAP 停止條件(範圍: 0-1)
            this.iocp.mip_gap = 0;

            // 整數容忍差(浮點數)
            this.iocp.tol_int = 1e-4;

            // 目標容忍差(浮點數)
            this.iocp.tol_obj = 1e-4;

            // 分支方法設定
            // GLPK.GLP_BR_FFV
            // GLPK.GLP_BR_LFV
            // GLPK.GLP_BR_MFV
            // GLPK.GLP_BR_DTH
            // GLPK.GLP_BR_PCH
            this.iocp.br_tech = GLPK.GLP_BR_FFV;

            // 設定訊息等級
            // GLPK.GLP_MSG_OFF: 禁止所有GLPK的輸出訊息
            // GLPK.GLP_MSG_ERR: 只輸出錯誤訊息
            // GLPK.GLP_MSG_ON : 輸出警告和錯誤訊息
            // GLPK.GLP_MSG_ALL: 輸出所有訊息
            this.iocp.msg_lev = GLPK.GLP_MSG_ALL;

            // 回朔技術
            // GLPK.GLP_BT_DFS
            // GLPK.GLP_BT_BFS
            // GLPK.GLP_BT_BLB
            // GLPK.GLP_BT_BPH
            this.iocp.bt_tech = GLPK.GLP_BT_DFS;

            // 啟發式演算法: GLPK.GLP_ON / GLPK.GLP_OFF
            this.iocp.fp_heur = GLPK.GLP_ON; // Feasibility Pump
            this.iocp.ps_heur = GLPK.GLP_ON; // Pivot and Shift
            this.iocp.sr_heur = GLPK.GLP_ON; // Shifted Rounding

            // Mixed-Integer Rounding (MIR) cuts: GLPK.GLP_ON / GLPK.GLP_OFF
            this.iocp.mir_cuts = GLPK.GLP_ON;

            // Gomory Cut: GLPK.GLP_ON / GLPK.GLP_OFF
            this.iocp.gmi_cuts = GLPK.GLP_ON;
        }

        public void solve()
        {
            try
            {
                // do not listen for terminal output anymore
                // 用於輸出GLPK的求解資訊於CMD上
                GlpkTerminal.removeListener(this);

                // Solve model
                ret = GLPK.glp_intopt(this.lp, this.iocp);

                // postsolve model
                if (ret == 0)
                {
                    GLPK.glp_mpl_postsolve(this.tran, this.lp, GLPK.GLP_MIP);
                }

                // free memory
                GLPK.glp_mpl_free_wksp(this.tran);
                GLPK.glp_delete_prob(this.lp);
            }
            catch (org.gnu.glpk.GlpkException e)
            {
                Console.Error.WriteLine("An error inside the GLPK library occured.");
                Console.Error.WriteLine(e.Message);
            }
            catch (ApplicationException e)
            {
                Console.Error.WriteLine(e.Message);
            }

            // Do not listen for callbacks anymore
            // 用於抓取使用GLPK的例外狀況
            GlpkCallback.removeListener(this);

            // check that the terinal hook function has been used
            if (!hookUsed)
            {
                throw new ApplicationException("The terminal output hook was not used.");
            }
        }

        public void CreateCV() 
        {
            int n  = GLPK.glp_get_num_cols(this.lp);
            GLPK.glp_add_cols(this.lp, n);
        }
        public void CreateIV()
        {

        }

        static void write_lp_solution(glp_prob lp)
        {
            int i;
            int n;
            String name;
            double val;

            name = GLPK.glp_get_obj_name(lp);
            val = GLPK.glp_get_obj_val(lp);
            Console.Write(name);
            Console.Write(" = ");
            Console.WriteLine(val);
            n = GLPK.glp_get_num_cols(lp);
            for (i = 1; i <= n; i++)
            {
                name = GLPK.glp_get_col_name(lp, i);
                val = GLPK.glp_get_col_prim(lp, i);
                Console.Write(name);
                Console.Write(" = ");
                Console.WriteLine(val);
            }
        }

        public void OutputSolution()
        {
            Console.WriteLine($"ret = {ret}; sol = {GLPK.doubleArray_getitem(this.doubleSol, 0)}");
        }

        public void DeleteProb() 
        {
            GLPK.glp_delete_prob(lp);
            GLPK.delete_doubleArray(doubleVar);
        }

        /// <summary>
        /// For IGlpkTerminalListener Interface
        /// </summary>
        /// <param name="str"></param>
        /// <returns></returns>
        public bool output(string str)
        {
            hookUsed = true;
            Console.Write(str);
            return false;
        }

        /// <summary>
        /// For IGlpkCallbackListener Interface
        /// </summary>
        /// <param name="tree"></param>
        public void callback(glp_tree tree)
        {
            int reason = GLPK.glp_ios_reason(tree);
            if (reason == GLPK.GLP_IBINGO)
            {
                Console.WriteLine("Better solution found");
            }
        }

        #region Dipose
        /// <summary>
        /// 自動釋放資源
        /// https://www.cnblogs.com/luminji/archive/2011/01/05/1926468.html
        /// https://www.huanlintalk.com/2022/09/csharp-exception-handling.html
        /// </summary>
        public void Dispose()
        {
            this.Dispose(true);
            GC.SuppressFinalize(this);
        }
        protected virtual void Dispose(bool disposing)
        {
            if (disposing)
            {
                //执行基本的清理代码
            }
        }
        ~GLPKBasic()
        {
            this.Dispose(false);
        }
        #endregion
    }
}

```

```csharp
using System;
using System.Collections.Generic;
using System.Data.Common;
using System.IO;
using System.Linq;
using org.gnu.glpk;

namespace AutoCut
{
    public class Program
    {
        static void Main(string[] args)
        {
            double MaxValue = 1E7;

            double ACT = 150;
            double[] Plan = new double[] { 100, 100, 100, 0, 0, 100, 100, 0, 0 };

            glp_prob lp;
            glp_smcp parm;
            SWIGTYPE_p_int ind;
            SWIGTYPE_p_double val;
            int ret;

            // 創建問題
            lp = GLPK.glp_create_prob();
            GLPK.glp_set_prob_name(lp, "Mixed Integer Programming Example");

            Dictionary<string, int> X_Variable_Pool = new Dictionary<string, int>();
            Dictionary<string, int> Y_Variable_Pool = new Dictionary<string, int>();
            Dictionary<string, int> Constraints_Pool = new Dictionary<string, int>();

            // 建立變數
            int VarNum = 0;
            for (int i = 1; i <= Plan.Length; i++)
            {
                GLPK.glp_add_cols(lp, 1);
                ++VarNum;
                X_Variable_Pool[$"X_Variable@Day{i}"] = VarNum;
            }

            for (int i = 1; i <= Plan.Length; i++)
            {
                GLPK.glp_add_cols(lp, 1);
                ++VarNum;
                Y_Variable_Pool[$"Y_Variable@Day{i}"] = VarNum;
            }

            // 建立連續變數
            // GLPK.GLP_CV：連續變量（Continuous Variable）。默認變量類型。
            // GLPK.GLP_IV：整數變量（Integer Variable）。
            // GLPK.GLP_BV：二元變量（Binary Variable）。

            // GLPK.GLP_FR：自由變量或約束（沒有上下界）。
            // GLPK.GLP_LO：有下界但沒有上界。
            // GLPK.GLP_UP：有上界但沒有下界。
            // GLPK.GLP_DB：有上下界。
            // GLPK.GLP_FX：固定值。

            foreach (var var in X_Variable_Pool)
            {
                GLPK.glp_set_col_name(lp, var.Value, var.Key);
                GLPK.glp_set_col_kind(lp, var.Value, GLPK.GLP_CV);
                GLPK.glp_set_col_bnds(lp, var.Value, GLPK.GLP_DB, 0, MaxValue);
            }

            // 建立二元變數
            foreach (var var in Y_Variable_Pool)
            {
                GLPK.glp_set_col_name(lp, var.Value, var.Key);
                GLPK.glp_set_col_kind(lp, var.Value, GLPK.GLP_BV);
                GLPK.glp_set_col_bnds(lp, var.Value, GLPK.GLP_DB, 0, 1);
            }
            // ====================================================================

            #region 切帳日限制式
            Constraints_Pool["CutDayPlan"] = Constraints_Pool.Count + 1;
            GLPK.glp_add_rows(lp, 1);
            GLPK.glp_set_row_name(lp, Constraints_Pool["CutDayPlan"], "CutDayPlan");
            GLPK.glp_set_row_bnds(lp, Constraints_Pool["CutDayPlan"], GLPK.GLP_FX, ACT, ACT);

            ind = GLPK.new_intArray(1);
            val = GLPK.new_doubleArray(1);

            GLPK.intArray_setitem(ind, 1, 1); GLPK.doubleArray_setitem(val, 1, 1);
            GLPK.glp_set_mat_row(lp, Constraints_Pool["CutDayPlan"], 1, ind, val);

            GLPK.delete_intArray(ind);
            GLPK.delete_doubleArray(val);
            #endregion

            #region 依需求投產限制式
            double SumDemand = Plan.Sum();
            Constraints_Pool["DemandAllocation"] = Constraints_Pool.Count + 1;
            GLPK.glp_add_rows(lp, 1);
            GLPK.glp_set_row_name(lp, Constraints_Pool["DemandAllocation"], "DemandAllocation");
            GLPK.glp_set_row_bnds(lp, Constraints_Pool["DemandAllocation"], GLPK.GLP_FX, SumDemand, SumDemand);

            ind = GLPK.new_intArray(X_Variable_Pool.Count + 1);
            val = GLPK.new_doubleArray(X_Variable_Pool.Count + 1);

            int idx = 1;
            foreach (var var in X_Variable_Pool)
            {
                GLPK.intArray_setitem(ind, idx, var.Value);  // 在限制式中，屬於第幾個變數，該變數的 Index 為多少
                GLPK.doubleArray_setitem(val, idx, 1);       // 在限制式中，屬於第幾個變數，該變數的 Value 為多少
                idx++;
            }
            GLPK.glp_set_mat_row(lp, Constraints_Pool["DemandAllocation"], X_Variable_Pool.Count, ind, val);

            GLPK.delete_intArray(ind);
            GLPK.delete_doubleArray(val);
            #endregion

            #region 變動調整限制式
            // Y 變數設定
            for (int day = 1; day <= Plan.Length; day++)
            {
                Constraints_Pool[$"YLogic@{day}"] = Constraints_Pool.Count + 1;
                GLPK.glp_add_rows(lp, 1);
                GLPK.glp_set_row_name(lp, Constraints_Pool[$"YLogic@{day}"], $"YLogic@{day}");
                GLPK.glp_set_row_bnds(lp, Constraints_Pool[$"YLogic@{day}"], GLPK.GLP_UP, MaxValue, MaxValue); // <= 限制

                ind = GLPK.new_intArray(Plan.Length - day + 2);
                val = GLPK.new_doubleArray(Plan.Length - day + 2);

                idx = 0;
                for (int i = day + 1; i <= Plan.Length; i++)
                {
                    ++idx; // 從 1 開始
                    GLPK.intArray_setitem(ind, idx, X_Variable_Pool[$"X_Variable@Day{i}"]);  // 在限制式中，屬於第幾個變數，該變數的 Index 為多少
                    GLPK.doubleArray_setitem(val, idx, 1);                                   // 在限制式中，屬於第幾個變數，該變數的 Value 為多少
                }

                ++idx;
                GLPK.intArray_setitem(ind, Plan.Length - day + 1, Y_Variable_Pool[$"Y_Variable@Day{day}"]);    // 在限制式中，屬於第幾個變數，該變數的 Index 為多少
                GLPK.doubleArray_setitem(val, Plan.Length - day + 1, MaxValue);                                // 在限制式中，屬於第幾個變數，該變數的 Value 為多少
                GLPK.glp_set_mat_row(lp, Constraints_Pool.Count, idx, ind, val);
                GLPK.delete_intArray(ind);
                GLPK.delete_doubleArray(val);
            }
            #endregion

            #region 限制產能下界
            for (int day = 2; day <= Plan.Length; day++)
            {
                double Q = Plan[day - 1];

                Constraints_Pool[$"LB@{day}"] = Constraints_Pool.Count + 1;
                GLPK.glp_add_rows(lp, 1);
                GLPK.glp_set_row_name(lp, Constraints_Pool[$"LB@{day}"], $"LB@{day}");
                GLPK.glp_set_row_bnds(lp, Constraints_Pool[$"LB@{day}"], GLPK.GLP_UP, -Q, -Q); // <= 限制

                ind = GLPK.new_intArray(3);
                val = GLPK.new_doubleArray(3);

                GLPK.intArray_setitem(ind, 1, X_Variable_Pool[$"X_Variable@Day{day}"]);
                GLPK.doubleArray_setitem(val, 1, -1);

                GLPK.intArray_setitem(ind, 2, Y_Variable_Pool[$"Y_Variable@Day{day}"]);
                GLPK.doubleArray_setitem(val, 2, -Q);

                GLPK.glp_set_mat_row(lp, Constraints_Pool.Count, 2, ind, val);

                GLPK.delete_intArray(ind);
                GLPK.delete_doubleArray(val);
            }
            #endregion

            #region 限制產能上界
            for (int day = 2; day <= Plan.Length; day++)
            {
                double Q = Plan[day - 1];

                Constraints_Pool[$"UB@{day}"] = Constraints_Pool.Count + 1;
                GLPK.glp_add_rows(lp, 1);
                GLPK.glp_set_row_name(lp, Constraints_Pool[$"UB@{day}"], $"UB@{day}");
                GLPK.glp_set_row_bnds(lp, Constraints_Pool[$"UB@{day}"], GLPK.GLP_UP, 100, 100); // <= 限制

                ind = GLPK.new_intArray(2);
                val = GLPK.new_doubleArray(2);

                GLPK.intArray_setitem(ind, 1, X_Variable_Pool[$"X_Variable@Day{day}"]);
                GLPK.doubleArray_setitem(val, 1, 1);

                GLPK.glp_set_mat_row(lp, Constraints_Pool.Count, 1, ind, val);

                GLPK.delete_intArray(ind);
                GLPK.delete_doubleArray(val);
            }
            #endregion

            #region 目標式
            // Define objective
            GLPK.glp_set_obj_name(lp, "z");
            GLPK.glp_set_obj_dir(lp, GLPK.GLP_MIN);
            //GLPK.glp_set_obj_coef(lp, VarIndex, Coefficient);

            // Solve model
            parm = new glp_smcp();
            GLPK.glp_init_smcp(parm);
            ret = GLPK.glp_simplex(lp, parm);

            // 將模型輸出為.lp文件
            string lpFilePath = "model.lp";
            PrintLP(lp, lpFilePath);

            // Retrieve solution
            if (ret == 0)
            {
                write_lp_solution(lp);
            }
            else
            {
                Console.WriteLine("The problem could not be solved");
            }

            #endregion

            // Free memory
            GLPK.glp_delete_prob(lp);

            Console.ReadLine();

        }

        static void write_lp_solution(glp_prob lp)
        {
            int i;
            int n;
            String name;
            double val;

            name = GLPK.glp_get_obj_name(lp);
            val = GLPK.glp_get_obj_val(lp);
            Console.Write(name);
            Console.Write(" = ");
            Console.WriteLine(val);
            n = GLPK.glp_get_num_cols(lp);
            for (i = 1; i <= n; i++)
            {
                name = GLPK.glp_get_col_name(lp, i);
                val = GLPK.glp_get_col_prim(lp, i);
                Console.Write(name);
                Console.Write(" = ");
                Console.WriteLine(val);
            }
        }
        /// <summary>
        /// 輸出 .lp 檔
        /// </summary>
        /// <param name="lp"></param>
        /// <param name="filePath"></param>
        public static void PrintLP(glp_prob lp, string filePath)
        {
            using (StreamWriter writer = new StreamWriter(filePath))
            {
                // Objective function
                writer.Write("Maximize\n z:");
                int numCols = GLPK.glp_get_num_cols(lp);
                for (int i = 1; i <= numCols; i++)
                {
                    double coef = GLPK.glp_get_obj_coef(lp, i);
                    string name = GLPK.glp_get_col_name(lp, i);
                    writer.Write($" + {coef} {name}");
                }
                writer.WriteLine();

                // Subject to
                writer.WriteLine("Subject To");
                int numRows = GLPK.glp_get_num_rows(lp);
                for (int i = 1; i <= numRows; i++)
                {
                    string name = GLPK.glp_get_row_name(lp, i);
                    int numElems = GLPK.glp_get_mat_row(lp, i, null, null);
                    SWIGTYPE_p_int ind = GLPK.new_intArray(numElems + 1);
                    SWIGTYPE_p_double val = GLPK.new_doubleArray(numElems + 1);
                    GLPK.glp_get_mat_row(lp, i, ind, val);
                    double lb = GLPK.glp_get_row_lb(lp, i);
                    double ub = GLPK.glp_get_row_ub(lp, i);

                    writer.Write($"{name}: ");
                    for (int j = 1; j <= numElems; j++)
                    {
                        int idx = GLPK.intArray_getitem(ind, j);
                        double coef = GLPK.doubleArray_getitem(val, j);
                        string varName = GLPK.glp_get_col_name(lp, idx);
                        writer.Write($" + {coef} {varName}");
                    }
                    if (lb == ub)
                        writer.WriteLine($" = {lb}");
                    else if (ub == double.PositiveInfinity)
                        writer.WriteLine($" >= {lb}");
                    else if (lb == double.NegativeInfinity)
                        writer.WriteLine($" <= {ub}");
                    else
                        writer.WriteLine($" <= {ub}");
                }

                // Bounds
                writer.WriteLine("Bounds");
                for (int i = 1; i <= numCols; i++)
                {
                    string name = GLPK.glp_get_col_name(lp, i);
                    double lb = GLPK.glp_get_col_lb(lp, i);
                    double ub = GLPK.glp_get_col_ub(lp, i);
                    writer.WriteLine($"{lb} <= {name} <= {ub}");
                }

                // End
                writer.WriteLine("End");
            }
        }
    }
}

```