package ru.cyclone.susc_tumbler;

import androidx.compose.foundation.layout.Arrangement;
import androidx.compose.foundation.layout.ColumnKt;
import androidx.compose.foundation.layout.ColumnScope;
import androidx.compose.foundation.layout.ColumnScopeInstance;
import androidx.compose.foundation.layout.SizeKt;
import androidx.compose.runtime.Applier;
import androidx.compose.runtime.ComposablesKt;
import androidx.compose.runtime.Composer;
import androidx.compose.runtime.ComposerKt;
import androidx.compose.runtime.CompositionLocalMap;
import androidx.compose.runtime.Updater;
import androidx.compose.ui.Alignment;
import androidx.compose.ui.ComposedModifierKt;
import androidx.compose.ui.Modifier;
import androidx.compose.ui.layout.MeasurePolicy;
import androidx.compose.ui.node.ComposeUiNode;
import kotlin.Metadata;
import kotlin.Unit;
import kotlin.jvm.functions.Function0;
import kotlin.jvm.functions.Function1;
import kotlin.jvm.functions.Function2;
import kotlin.jvm.internal.Intrinsics;

/* JADX INFO: renamed from: ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt$lambda-5$1, reason: invalid class name */
/* JADX INFO: compiled from: MainActivity.kt */
/* JADX INFO: loaded from: /tmp/decompiler/1fff03f604024d51870ca7c74eae34df/classes2.dex */
@Metadata(k = 3, mv = {2, 0, 0}, xi = 48)
final class ComposableSingletons$MainActivityKt$lambda5$1 implements Function2<Composer, Integer, Unit> {
    public static final ComposableSingletons$MainActivityKt$lambda5$1 INSTANCE = new ComposableSingletons$MainActivityKt$lambda5$1();

    ComposableSingletons$MainActivityKt$lambda5$1() {
    }

    @Override // kotlin.jvm.functions.Function2
    public /* bridge */ /* synthetic */ Unit invoke(Composer composer, Integer num) {
        invoke(composer, num.intValue());
        return Unit.INSTANCE;
    }

    public final void invoke(Composer composer, int i) {
        ComposerKt.sourceInformation(composer, "C518@21369L811:MainActivity.kt#6o5wwo");
        if ((i & 3) != 2 || !composer.getSkipping()) {
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventStart(-325203374, i, -1, "ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt.lambda-5.<anonymous> (MainActivity.kt:518)");
            }
            Modifier modifierFillMaxSize$default = SizeKt.fillMaxSize$default(Modifier.Companion, 0.0f, 1, (Object) null);
            ComposerKt.sourceInformationMarkerStart(composer, -483455358, "CC(Column)P(2,3,1)85@4251L61,86@4317L133:Column.kt#2w3rfo");
            MeasurePolicy measurePolicyColumnMeasurePolicy = ColumnKt.columnMeasurePolicy(Arrangement.INSTANCE.getTop(), Alignment.Companion.getStart(), composer, 0);
            ComposerKt.sourceInformationMarkerStart(composer, -1323940314, "CC(Layout)P(!1,2)78@3182L23,81@3333L411:Layout.kt#80mrfh");
            int currentCompositeKeyHash = ComposablesKt.getCurrentCompositeKeyHash(composer, 0);
            CompositionLocalMap currentCompositionLocalMap = composer.getCurrentCompositionLocalMap();
            Modifier modifierMaterializeModifier = ComposedModifierKt.materializeModifier(composer, modifierFillMaxSize$default);
            Function0 constructor = ComposeUiNode.Companion.getConstructor();
            ComposerKt.sourceInformationMarkerStart(composer, -692256719, "CC(ReusableComposeNode)P(1,2)376@14062L9:Composables.kt#9igjgp");
            if (!(composer.getApplier() instanceof Applier)) {
                ComposablesKt.invalidApplier();
            }
            composer.startReusableNode();
            if (composer.getInserting()) {
                composer.createNode(constructor);
            } else {
                composer.useNode();
            }
            Composer composer2 = Updater.constructor-impl(composer);
            Updater.set-impl(composer2, measurePolicyColumnMeasurePolicy, ComposeUiNode.Companion.getSetMeasurePolicy());
            Updater.set-impl(composer2, currentCompositionLocalMap, ComposeUiNode.Companion.getSetResolvedCompositionLocals());
            Function2 setCompositeKeyHash = ComposeUiNode.Companion.getSetCompositeKeyHash();
            if (composer2.getInserting() || !Intrinsics.areEqual(composer2.rememberedValue(), Integer.valueOf(currentCompositeKeyHash))) {
                composer2.updateRememberedValue(Integer.valueOf(currentCompositeKeyHash));
                composer2.apply(Integer.valueOf(currentCompositeKeyHash), setCompositeKeyHash);
            }
            Updater.set-impl(composer2, modifierMaterializeModifier, ComposeUiNode.Companion.getSetModifier());
            ComposerKt.sourceInformationMarkerStart(composer, -384862393, "C87@4365L9:Column.kt#2w3rfo");
            ColumnScope columnScope = ColumnScopeInstance.INSTANCE;
            ComposerKt.sourceInformationMarkerStart(composer, -1929582119, "C523@21605L3,524@21643L3,525@21679L3,526@21717L3,519@21425L406:MainActivity.kt#6o5wwo");
            composer.startReplaceGroup(-1586260220);
            ComposerKt.sourceInformation(composer, "CC(remember):MainActivity.kt#9igjgp");
            Object objRememberedValue = composer.rememberedValue();
            if (objRememberedValue == Composer.Companion.getEmpty()) {
                objRememberedValue = new Function1() { // from class: ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt$lambda-5$1$$ExternalSyntheticLambda0
                    @Override // kotlin.jvm.functions.Function1
                    public final Object invoke(Object obj) {
                        return ComposableSingletons$MainActivityKt$lambda5$1.invoke$lambda$8$lambda$1$lambda$0(((Integer) obj).intValue());
                    }
                };
                composer.updateRememberedValue(objRememberedValue);
            }
            Function1 function1 = (Function1) objRememberedValue;
            composer.endReplaceGroup();
            composer.startReplaceGroup(-1586259004);
            ComposerKt.sourceInformation(composer, "CC(remember):MainActivity.kt#9igjgp");
            Object objRememberedValue2 = composer.rememberedValue();
            if (objRememberedValue2 == Composer.Companion.getEmpty()) {
                objRememberedValue2 = new Function0() { // from class: ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt$lambda-5$1$$ExternalSyntheticLambda1
                    @Override // kotlin.jvm.functions.Function0
                    public final Object invoke() {
                        return Unit.INSTANCE;
                    }
                };
                composer.updateRememberedValue(objRememberedValue2);
            }
            Function0 function0 = (Function0) objRememberedValue2;
            composer.endReplaceGroup();
            composer.startReplaceGroup(-1586257852);
            ComposerKt.sourceInformation(composer, "CC(remember):MainActivity.kt#9igjgp");
            Object objRememberedValue3 = composer.rememberedValue();
            if (objRememberedValue3 == Composer.Companion.getEmpty()) {
                objRememberedValue3 = new Function1() { // from class: ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt$lambda-5$1$$ExternalSyntheticLambda2
                    @Override // kotlin.jvm.functions.Function1
                    public final Object invoke(Object obj) {
                        return ComposableSingletons$MainActivityKt$lambda5$1.invoke$lambda$8$lambda$5$lambda$4(((Boolean) obj).booleanValue());
                    }
                };
                composer.updateRememberedValue(objRememberedValue3);
            }
            Function1 function12 = (Function1) objRememberedValue3;
            composer.endReplaceGroup();
            composer.startReplaceGroup(-1586256636);
            ComposerKt.sourceInformation(composer, "CC(remember):MainActivity.kt#9igjgp");
            Object objRememberedValue4 = composer.rememberedValue();
            if (objRememberedValue4 == Composer.Companion.getEmpty()) {
                objRememberedValue4 = new Function1() { // from class: ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt$lambda-5$1$$ExternalSyntheticLambda3
                    @Override // kotlin.jvm.functions.Function1
                    public final Object invoke(Object obj) {
                        return ComposableSingletons$MainActivityKt$lambda5$1.invoke$lambda$8$lambda$7$lambda$6(((Boolean) obj).booleanValue());
                    }
                };
                composer.updateRememberedValue(objRememberedValue4);
            }
            composer.endReplaceGroup();
            MainActivityKt.SuscTumblerContent(false, false, null, function1, function0, function12, (Function1) objRememberedValue4, SizeKt.wrapContentSize$default(ColumnScope.weight$default(columnScope, SizeKt.fillMaxWidth$default(Modifier.Companion, 0.0f, 1, (Object) null), 1.0f, false, 2, (Object) null), Alignment.Companion.getCenter(), false, 2, (Object) null), composer, 1797558, 0);
            composer.startReplaceGroup(-1586252249);
            ComposerKt.sourceInformation(composer, "530@21885L19,532@22007L149");
            composer.endReplaceGroup();
            ComposerKt.sourceInformationMarkerEnd(composer);
            ComposerKt.sourceInformationMarkerEnd(composer);
            composer.endNode();
            ComposerKt.sourceInformationMarkerEnd(composer);
            ComposerKt.sourceInformationMarkerEnd(composer);
            ComposerKt.sourceInformationMarkerEnd(composer);
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventEnd();
                return;
            }
            return;
        }
        composer.skipToGroupEnd();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final Unit invoke$lambda$8$lambda$1$lambda$0(int i) {
        return Unit.INSTANCE;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final Unit invoke$lambda$8$lambda$5$lambda$4(boolean z) {
        return Unit.INSTANCE;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final Unit invoke$lambda$8$lambda$7$lambda$6(boolean z) {
        return Unit.INSTANCE;
    }
}
